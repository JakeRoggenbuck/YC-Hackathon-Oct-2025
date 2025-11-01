import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

def _build_messages(test_results: str) -> List[Dict[str, str]]:
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert API testing engineer.
Extract and analyze ALL errors found in the test results with thorough detail.

For each error, provide:
1. Route/Endpoint
2. Error Code (HTTP status + meaning)
3. Input Cause (what triggered it)
4. GitHub Location (file:line if known)
5. Technical Context (stack trace / error text)
6. Impact
7. Fix (action plan)

At the end of your response, OUTPUT a single JSON object of the form:
{{"issues":[
  {{
    "title": "Concise bug title",
    "body": "Markdown body with details, impact, and fix steps",
    "repo": "owner/repo",
    "labels": ["bug","api","auto-filed"],
    "assignees": []
  }}
]}}
Do not wrap the JSON in backticks.
"""),
        ("human", """Analyze these API test results and extract ALL errors:

=== API TEST RESULTS ===
{test_results}

Skip passing tests. Be ruthless about failures.""")
    ])

    return prompt_template.format_messages(
        test_results=test_results or "[No test results provided]"
    )


def _parse_issues_from_text(model_text: str) -> List[Dict[str, Any]]:
    start = model_text.rfind('"issues"')
    if start == -1:
        return []
    obj_start = model_text.rfind("{", 0, start)
    if obj_start == -1:
        return []
    for end in range(len(model_text), obj_start, -1):
        chunk = model_text[obj_start:end]
        try:
            payload = json.loads(chunk)
            issues = payload.get("issues", [])
            if isinstance(issues, list):
                return issues
        except Exception:
            pass
    return []


def _parse_github_repo(repo_string: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse a GitHub repository string and extract owner and repo name.
    
    Handles formats:
    - "owner/repo" -> ("owner", "repo")
    - "https://github.com/owner/repo" -> ("owner", "repo")
    - "https://github.com/owner/repo.git" -> ("owner", "repo")
    
    Returns:
        Tuple of (owner, repo) or (None, None) if parsing fails
    """
    if not repo_string:
        return None, None
    
    repo_string = repo_string.strip()
    
    # Remove .git suffix if present
    if repo_string.endswith(".git"):
        repo_string = repo_string[:-4]
    
    # Handle full GitHub URL
    if "github.com" in repo_string:
        # Extract path after github.com/
        try:
            # Remove protocol if present
            if "://" in repo_string:
                repo_string = repo_string.split("://", 1)[1]
            
            # Remove github.com/ prefix
            if "github.com/" in repo_string:
                repo_string = repo_string.split("github.com/", 1)[1]
            
            # Remove any trailing slashes or additional path segments
            parts = repo_string.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        except Exception:
            pass
    
    # Handle simple "owner/repo" format
    if "/" in repo_string:
        parts = repo_string.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    
    return None, None


async def _open_github_issues_with_mcp(
    issues: List[Dict[str, Any]],
    mcp_url: str,
) -> List[Tuple[Dict[str, Any], Optional[Any], Optional[str]]]:
    """
    Connect to Composio MCP server, find a GitHub 'create issue' tool,
    and call it for each parsed issue.
    Returns [(issue_spec, tool_response, error_string_or_None), ...]
    """

    results: List[Tuple[Dict[str, Any], Optional[Any], Optional[str]]] = []

    # Create the MCP client. We're telling it "there is a server called 'composio'",
    # reachable via SSE/HTTP ("streamable_http") at mcp_url.
    client = MultiServerMCPClient(
        {
            "composio": {
                "transport": "streamable_http",
                "url": mcp_url,
            }
        }
    )

    try:
        # 1. Get tools from that server.
        # In this version of the library, get_tools() doesn't take server name argument
        tools = await client.get_tools()

        # 2. Find a tool that looks like "create issue"
        def pick_issue_tool():
            for tool in tools:
                nm = tool.name.lower()
                if "issue" in nm and ("create" in nm or "open" in nm):
                    return tool
            # fallback: any tool mentioning "issue"
            for tool in tools:
                if "issue" in tool.name.lower():
                    return tool
            return None

        create_issue_tool = pick_issue_tool()
        if create_issue_tool is None:
            raise RuntimeError("No GitHub create-issue tool exposed by MCP (check your Composio server config)")

        # 3. Call that tool for each issue Gemini proposed
        for spec in issues:
            try:
                # Parse the repo string (handles URLs and "owner/repo" format)
                repo_full = (spec.get("repo") or "").strip()
                owner, repo = _parse_github_repo(repo_full)
                
                if not owner or not repo:
                    raise ValueError(f"Could not parse repository from: {repo_full}")

                payload = {
                    "owner": owner,
                    "repo": repo,
                    "title": spec.get("title") or "Automated issue",
                    "body": spec.get("body") or "",
                    "labels": spec.get("labels") or ["bug", "api"],
                    "assignees": spec.get("assignees") or [],
                }

                # strip empty values except body (GitHub usually requires title/body, others optional)
                payload = {
                    k: v for k, v in payload.items()
                    if v not in (None, "", []) or k == "body"
                }

                resp = await create_issue_tool.ainvoke(payload)
                results.append((spec, resp, None))
            except Exception as e:
                results.append((spec, None, str(e)))

    finally:
        # This cleans up any open sessions/sockets
        try:
            await client.close()
        except Exception:
            pass

    return results


async def analyze_api_tests(test_results: str, target_repo: str = None) -> Dict[str, Any]:
    """
    1. Ask AI to analyze API test logs.
    2. Parse out structured issues.
    3. (If COMPOSIO_MCP_URL is set) create GitHub issues via Composio MCP.
    
    Args:
        test_results: The test output to analyze
        target_repo: Optional GitHub repo in "owner/repo" format to assign to all issues
    """
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")

    # Gemini analysis
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )

    # PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
    # if not PERPLEXITY_API_KEY:
    #     raise ValueError("PERPLEXITY_API_KEY not found in environment variables. Please set it in .env file.")

    # # Initialize Perplexity model via LangChain (using OpenAI-compatible interface)
    # llm = ChatOpenAI(
    #     model="sonar",
    #     openai_api_key=PERPLEXITY_API_KEY,
    #     openai_api_base="https://api.perplexity.ai",
    #     temperature=0.2,
    # )

    messages = _build_messages(test_results)
    gemini_resp = llm.invoke(messages)
    analysis_text = getattr(gemini_resp, "content", str(gemini_resp))

    # --- 2. Extract issues JSON
    issues = _parse_issues_from_text(analysis_text)
    
    # --- 2.5. Set target repo on all issues if provided (must be done BEFORE MCP call)
    if target_repo:
        for issue in issues:
            issue["repo"] = target_repo

    # --- 3. Try MCP -> GitHub
    issue_results: List[Tuple[Dict[str, Any], Optional[Any], Optional[str]]] = []
    mcp_url = os.getenv("COMPOSIO_MCP_URL", "").strip()
    if mcp_url and issues:
        try:
            issue_results = await _open_github_issues_with_mcp(issues, mcp_url)
        
        except Exception as e:
            issue_results = [
                (
                    {"title": "(MCP error)"},
                    None,
                    f"MCP failed: {e}"
                )
            ]
    else:
        if not mcp_url:
            issue_results = [
                (
                    {"title": "(MCP skipped)"},
                    None,
                    "COMPOSIO_MCP_URL not set, so no GitHub issues were opened."
                )
            ]

    return {
        "analysis": analysis_text,
        "issues": issues,
        "issue_results": issue_results,
    }
