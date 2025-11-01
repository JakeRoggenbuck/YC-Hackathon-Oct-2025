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
    print("🔍 Analyzing API test results with AI...")
    response = llm.invoke(messages)
    
    return {
        "analysis": response.content,
    }


def generate_email(analysis: str, recipient: str = "team@example.com") -> Dict[str, str]:
    """
    Generate email content as strict JSON for Gmail with Crash Test branding.
    Returns dict with subject, text, and html fields.
    """
    
    email_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are writing a friendly, professional HTML email from a coworker about API testing errors.

CRITICAL: You MUST return ONLY a valid JSON object with these exact fields:
{
  "subject": "string - email subject line",
  "text": "string - plain text version of email body",
  "html": "string - HTML formatted email with styling"
}

HTML REQUIREMENTS:
1. Start with Crash Test header: <div class="email-header" style="background: hsl(342, 85.11%, 52.55%); padding: 20px; text-align: center; margin-bottom: 20px;"><h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Crash Test</h1></div>
2. Add a friendly greeting like "Hello, here is your report..."
3. Use proper HTML formatting with inline CSS for Gmail compatibility
4. Use clean typography (Arial, sans-serif)
5. Use bullet points (•) and proper indentation
6. Use bold for emphasis on key terms
7. Use subtle colors: red for errors, blue for info
8. Tone: friendly coworker, not overly formal

For each error section:
- Bold the route and error code
- Use bullet points for details
- Keep fix instructions clear and actionable

DO NOT include any text outside the JSON object. Return ONLY valid JSON."""),
        ("human", """Create a JSON email based on this API test analysis:

{analysis}

Recipient: {recipient}

Return ONLY this JSON structure (no other text):
{{
  "subject": "Your subject line here",
  "text": "Plain text version with greeting, summary, and error list",
  "html": "<div class='email-header' style='background: hsl(342, 85.11%, 52.55%); padding: 20px; text-align: center; margin-bottom: 20px;'><h1 style='color: white; margin: 0; font-size: 28px; font-weight: 600;'>Crash Test</h1></div><div style='font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px;'><p style='font-size: 16px;'>Friendly greeting...</p><p style='font-size: 14px; color: #666;'>Brief summary</p><h3 style='color: #d32f2f; margin-top: 24px;'>Errors Found:</h3>Error details with bullets and styling</div>"
}}

Make text version readable without HTML. Make HTML feel like a helpful coworker sharing test results.""")
    ])
    
    messages = email_prompt.format_messages(
        analysis=analysis,
        recipient=recipient
    )
    
    print("✉️  Generating email content...")
    response = llm.invoke(messages)
    
    # Parse JSON response
    import json
    try:
        # Extract JSON from response (in case there's extra text)
        content = response.content.strip()
        
        # Try to find JSON object in response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            email_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['subject', 'text', 'html']
            if all(field in email_data for field in required_fields):
                return email_data
            else:
                raise ValueError(f"Missing required fields. Got: {list(email_data.keys())}")
        else:
            raise ValueError("No JSON object found in response")
            
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parsing error: {e}")
        print(f"Raw response: {content[:500]}...")
        raise ValueError(f"Failed to parse JSON from AI response: {e}")
    except Exception as e:
        print(f"⚠️  Error processing response: {e}")
        raise


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
    email_data = generate_email(
        analysis=analysis_result["analysis"],
        recipient="engineering-team@company.com"
    )
    
    print("\n" + "=" * 60)
    print("📧 GENERATED EMAIL")
    print("=" * 60)
    print(f"Subject: {email_data['subject']}")
    print(f"\nText Version:\n{email_data['text'][:200]}...")
    print(f"\nHTML Version:\n{email_data['html'][:200]}...")
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
        f.write(f"Subject: {email_data['subject']}\n\n")
        f.write("TEXT VERSION:\n")
        f.write(email_data['text'])
        f.write("\n\n" + "-" * 60 + "\n\n")
        f.write("HTML VERSION:\n")
        f.write(email_data['html'])
    
    print(f"✅ Output saved to: {output_path}")
    
    # Save JSON for chaining to send_email
    json_output_path = backend_dir / "email_output.json"
    import json
    with open(json_output_path, 'w') as f:
        json.dump(email_data, f, indent=2)
    
    print(f"✅ JSON output saved to: {json_output_path}")
    print()


if __name__ == "__main__":
    main()
