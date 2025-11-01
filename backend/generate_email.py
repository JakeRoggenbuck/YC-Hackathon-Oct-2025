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


def generate_email(analysis: str, recipient: str = "team@example.com") -> str:
    """
    Generate a professional HTML email formatted for Gmail with Recompile branding.
    """
    
    email_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are writing a friendly, professional HTML email from a coworker about API testing errors.

CRITICAL REQUIREMENTS:
1. Start with Recompile header at the very top: <div class="email-header"><h1>Recompile</h1></div>
2. Add a friendly greeting like "Hello, here is your report..." or "Hi there, your API test results are in..."
3. Use proper HTML formatting with inline CSS for Gmail compatibility
4. Use clean typography (Arial, sans-serif)
5. Use bullet points (•) and proper indentation
6. Use bold for emphasis on key terms
7. Use subtle colors: red for errors, blue for info
8. Tone: friendly coworker, not overly formal

HTML Structure:
- Recompile header with styling (background, padding, centered text)
- Friendly greeting paragraph
- Brief summary (1-2 sentences)
- Error details with bullet points and styling
- Use <strong> for bold, <span style="color: #..."> for colors
- Add proper spacing and margins

For each error section:
- Bold the route and error code
- Use bullet points for details
- Keep fix instructions clear and actionable"""),
        ("human", """Create a Gmail-formatted HTML email based on this API test analysis:

{analysis}

Recipient: {recipient}

Format as:
Subject: [Your subject line]
---
<div class="email-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; margin-bottom: 20px;">
  <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Recompile</h1>
</div>

<div style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px;">
  <p style="font-size: 16px;">[Friendly greeting like "Hello, here is your report..." or similar]</p>
  <p style="font-size: 14px; color: #666;">[Brief summary]</p>
  
  <h3 style="color: #d32f2f; margin-top: 24px;">Errors Found:</h3>
  [Error details with bullets, colors, and styling]
</div>

Make it feel like a helpful coworker sharing test results, not a formal report.""")
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
