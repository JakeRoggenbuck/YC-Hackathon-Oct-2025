"""
Email generation script using LangChain + Google Gemini.
Analyzes API testing results and generates email as JSON output.
Returns: {"subject": "...", "text": "...", "html": "..."}
"""

import os
import json
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

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
Extract and analyze ALL errors found in the test results with thorough detail.

For each error, provide:
1. **Route/Endpoint**: The full API path (e.g., POST /api/testing_agent)
2. **Error Code**: HTTP status code (e.g., 500, 400, 422) with meaning
3. **Input Cause**: Detailed explanation of what input/condition triggered the error
4. **GitHub Location**: File path and line number if available
5. **Technical Context**: What went wrong technically (stack trace, error message)
6. **Impact**: How this affects users/API functionality
7. **Fix**: Detailed, actionable solution with code hints if relevant

Be thorough and technical. Provide enough context so developers understand the full picture."""),
        ("human", """Analyze these API test results and extract ALL errors with comprehensive details:

=== API TEST RESULTS ===
{test_results}

For each error, provide:
- Route/Endpoint
- Error Code and its meaning
- Detailed Input Cause (what data, why it broke)
- GitHub Location (if provided)
- Technical Context (error messages, stack traces)
- User Impact
- Detailed Fix (actionable steps)

Skip successful tests but be thorough on failures.""")
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


def generate_email_json(analysis: str) -> Dict[str, str]:
    """
    Generate email as strict JSON with subject, text, and html fields.
    Returns validated JSON dictionary.
    """
    
    email_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI that generates emails in STRICT JSON format.

You MUST return ONLY valid JSON with these exact fields:
{{
  "subject": "string - email subject line",
  "text": "string - plain text version of email",
  "html": "string - HTML email with Recompile branding"
}}

HTML Requirements:
1. Start with Recompile header: <div class="email-header" style="background: hsl(342, 85.11%, 52.55%); padding: 20px; text-align: center; margin-bottom: 20px;"><h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Recompile</h1></div>
2. Friendly greeting like "Hello, here is your report..."
3. Clean HTML with inline CSS for Gmail
4. Use Arial font, bullet points, proper spacing
5. Error details with: route, error code, input cause, location, fix

Text version: Simple plain text summary of the same content.

Return ONLY the JSON object, no markdown, no code blocks, no extra text."""),
        ("human", """Generate email JSON based on this API test analysis:

{analysis}

Return ONLY valid JSON with subject, text, and html fields.""")
    ])
    
    messages = email_prompt.format_messages(analysis=analysis)
    
    print("✉️  Generating email JSON...")
    response = llm.invoke(messages)
    
    # Parse and validate JSON
    try:
        # Clean the response (remove markdown code blocks if present)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        email_data = json.loads(content)
        
        # Validate required fields
        required_fields = ["subject", "text", "html"]
        for field in required_fields:
            if field not in email_data:
                raise ValueError(f"Missing required field: {field}")
        
        print("✅ JSON validation passed")
        return email_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response content: {response.content[:500]}...")
        raise ValueError(f"Failed to parse JSON from AI response: {e}")
    except Exception as e:
        print(f"❌ Validation error: {e}")
        raise


def main():
    """Main execution function - generates email JSON and optionally sends it."""
    print("=" * 60)
    print("📧 API Testing Email Generator - LangChain + Gemini")
    print("=" * 60)
    print()
    
    # Define test results file path
    script_dir = Path(__file__).parent
    test_results_path = script_dir / "test_results.txt"
    
    # Read test results
    print(f"📂 Reading API test results from: {test_results_path}")
    test_results = read_file(str(test_results_path))
    print()
    
    # Analyze test results
    analysis_result = analyze_api_tests(test_results)
    
    print("\n" + "=" * 60)
    print("📊 ANALYSIS RESULTS")
    print("=" * 60)
    print(analysis_result["analysis"][:500] + "..." if len(analysis_result["analysis"]) > 500 else analysis_result["analysis"])
    print()
    
    # Generate email JSON
    email_data = generate_email_json(analysis=analysis_result["analysis"])
    
    print("\n" + "=" * 60)
    print("📧 GENERATED EMAIL JSON")
    print("=" * 60)
    print(f"Subject: {email_data['subject']}")
    print(f"Text length: {len(email_data['text'])} chars")
    print(f"HTML length: {len(email_data['html'])} chars")
    print()
    
    # Save output
    output_json_path = script_dir / "email_output.json"
    with open(output_json_path, 'w') as f:
        json.dump(email_data, f, indent=2)
    
    print(f"✅ Email JSON saved to: {output_json_path}")
    print()
    
    return email_data


if __name__ == "__main__":
    main()
