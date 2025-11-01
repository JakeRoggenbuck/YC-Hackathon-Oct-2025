"""
Email generation script using LangChain + Google Gemini.
Analyzes API testing results (errors, metrics, status codes) and generates a summary email.
"""

import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")

# Initialize Gemini model via LangChain
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True  # Gemini requires this
)


def read_file(file_path: str) -> str:
    """Read a test results file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"[Test results file not found: {file_path}]"
    except Exception as e:
        return f"[Error reading {file_path}: {str(e)}]"


def analyze_api_tests(test_results: str) -> Dict[str, str]:
    """
    Analyze API testing results using Gemini.
    Returns a dictionary with analysis results.
    """
    
    # Create a comprehensive prompt for API test analysis
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert API testing engineer.
Extract and summarize ONLY the errors found in the test results.

For each error, identify:
1. **Route/Endpoint**: The API path (e.g., POST /api/testing_agent)
2. **Error Code**: HTTP status code (e.g., 500, 400, 422)
3. **Input Cause**: Specific input that triggered the error (e.g., "empty email string", "null value in apiUrl")
4. **GitHub Location**: File path and line number if available (e.g., validator.js:45)
5. **Fix**: Brief, actionable solution (1-2 sentences max)

Be concise and direct. Skip any passing tests."""),
        ("human", """Analyze these API test results and extract ONLY the errors:

=== API TEST RESULTS ===
{test_results}

List each error with:
- Route
- Error Code
- Input Cause
- GitHub Location (if provided)
- Fix (brief)

Skip successful tests.""")
    ])
    
    # Format the prompt with actual test data
    messages = prompt_template.format_messages(
        test_results=test_results or "[No test results provided]"
    )
    
    # Get analysis from Gemini
    print("🔍 Analyzing API test results with Gemini...")
    response = llm.invoke(messages)
    
    return {
        "analysis": response.content,
    }


def generate_email(analysis: str, recipient: str = "team@example.com") -> str:
    """
    Generate a short, concise email based on the API test analysis.
    """
    
    email_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are writing a SHORT, CONCISE technical email about API errors.

STRICT RULES:
- Start with a 1-2 sentence summary (how many errors, overall severity)
- Then list the errors in a clean format
- No fluff, greetings, or sign-offs

For each error, include ONLY:
1. Route/Endpoint (e.g., POST /api/testing_agent)
2. Error Code (e.g., 500, 400, etc.)
3. Input Cause (what data triggered it - be specific)
4. GitHub Location (file path and line number if available)
5. Fix (1-2 sentence solution)

Use bullet points or numbered list. Be direct."""),
        ("human", """Create a SHORT email based on this API test analysis:

{analysis}

Recipient: {recipient}

Format as:
Subject: [Your subject line]
---
[1-2 sentence summary]

[List the errors - no greeting, no closing remarks]""")
    ])
    
    messages = email_prompt.format_messages(
        analysis=analysis,
        recipient=recipient
    )
    
    print("✉️  Generating email content...")
    response = llm.invoke(messages)
    
    return response.content


def main():
    """Main execution function."""
    print("=" * 60)
    print("📧 API Testing Email Report - LangChain + Gemini")
    print("=" * 60)
    print()
    
    # Define test results file path (relative to script location)
    backend_dir = Path(__file__).parent
    test_results_path = backend_dir / "test_results.txt"
    
    # Read test results
    print(f"📂 Reading API test results from: {test_results_path}")
    test_results = read_file(str(test_results_path))
    print()
    
    # Analyze test results
    analysis_result = analyze_api_tests(test_results)
    
    print("\n" + "=" * 60)
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    print(analysis_result["analysis"])
    print()
    
    # Generate email
    email_content = generate_email(
        analysis=analysis_result["analysis"],
        recipient="engineering-team@company.com"
    )
    
    print("\n" + "=" * 60)
    print("📧 GENERATED EMAIL")
    print("=" * 60)
    print(email_content)
    print()
    
    # Save output
    output_path = backend_dir / "generated_email.txt"
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("API TEST ANALYSIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(analysis_result["analysis"])
        f.write("\n\n" + "=" * 60 + "\n")
        f.write("GENERATED EMAIL\n")
        f.write("=" * 60 + "\n\n")
        f.write(email_content)
    
    print(f"✅ Output saved to: {output_path}")
    print()


if __name__ == "__main__":
    main()
