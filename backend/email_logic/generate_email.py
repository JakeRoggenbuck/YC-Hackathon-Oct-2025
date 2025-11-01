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
  "subject": "string - MUST follow this format: 'API Test Report: X critical/major errors found in [endpoint_name]' (count the actual errors and use the main endpoint name from the analysis)",
  "text": "string - plain text version of email",
  "html": "string - HTML email with Recompile branding"
}}

SUBJECT LINE RULES:
- Format: "API Test Report: [number] [severity] errors found in [endpoint_name]"
- Example: "API Test Report: 5 critical errors found in /api/testing_agent"
- Example: "API Test Report: 3 major errors found in /api/users"
- Count the ACTUAL number of errors from the analysis
- Use the PRIMARY or MOST AFFECTED endpoint name (e.g., /api/testing_agent, /api/users)
- Use "critical" if there are 5xx errors, otherwise "major" or just "errors"
- If multiple endpoints, use the one with the most errors

HTML Requirements - Create a professional, clean email with this structure:

1. START with this exact header (copy exactly):
<div style="background: #ffffff; border-bottom: 2px solid #e5e5e5; padding: 24px 16px;">
  <div style="max-width: 600px; margin: 0 auto;">
    <h1 style="font-size: 28px; font-weight: 700; margin: 0; color: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
      Recompile
    </h1>
    <p style="font-size: 13px; color: #666; font-weight: 500; margin: 4px 0 0 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
      API Error Detection Report
    </p>
  </div>
</div>

2. Main content wrapper:
<div style="background: #f9fafb; padding: 32px 16px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden;">
    
3. Greeting section with padding:
<div style="padding: 24px; border-bottom: 1px solid #e5e5e5;">
  <p style="margin: 0; font-size: 15px; color: #374151; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
    Hello,
  </p>
  <p style="margin: 12px 0 0 0; font-size: 15px; color: #374151; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
    Your API testing has completed. Here's a summary of the findings:
  </p>
</div>

4. Summary section (brief overview):
<div style="padding: 24px; background: #fef3f2; border-left: 4px solid #ef4444;">
  <p style="margin: 0; font-size: 14px; font-weight: 600; color: #991b1b; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
    Summary: X errors detected across Y endpoints
  </p>
  <p style="margin: 8px 0 0 0; font-size: 13px; color: #7f1d1d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
    Brief 1-2 sentence overview of critical issues
  </p>
</div>

5. Error details section (each error in a card):
<div style="padding: 24px;">
  <h2 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
    Detailed Findings
  </h2>
  
  For EACH error, create a card like this:
  <div style="margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
    <div style="margin-bottom: 12px;">
      <span style="display: inline-block; padding: 4px 8px; background: #fee2e2; color: #991b1b; font-size: 12px; font-weight: 600; border-radius: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
        500 Internal Server Error
      </span>
    </div>
    <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600; color: #1f2937; font-family: 'SF Mono', Monaco, Consolas, monospace;">
      POST /api/endpoint
    </p>
    <p style="margin: 0 0 12px 0; font-size: 13px; color: #6b7280; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
      <strong>Cause:</strong> Brief description of what triggered the error
    </p>
    <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b7280; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
      <strong>Location:</strong> file.py:123
    </p>
    <p style="margin: 0; font-size: 13px; color: #059669; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
      <strong>Fix:</strong> Actionable solution
    </p>
  </div>
</div>

6. Footer:
<div style="padding: 20px 24px; background: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
  <p style="margin: 0; font-size: 12px; color: #9ca3af; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
    Generated by Recompile • API Error Detection
  </p>
</div>

CLOSE all divs properly.

Important styling rules:
- Use system fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial)
- Keep content width max 600px for email compatibility
- Use consistent spacing (padding: 24px, 16px)
- Error badges with colors: red (#fee2e2 bg, #991b1b text) for errors
- Monospace font for endpoints/code
- Clean card design with subtle shadows
- Proper hierarchy with font sizes (28px title, 18px h2, 15px body, 13-14px details)

Text version: Simple plain text summary of the same content.

CRITICAL: Return ONLY the raw JSON object. Do NOT wrap in markdown code blocks. Do NOT add any explanatory text before or after the JSON."""),
        ("human", """Generate email JSON based on this API test analysis:

{analysis}

IMPORTANT: Return ONLY the JSON object itself. No markdown formatting, no ```json, no code blocks, no extra text.

Just the raw JSON starting with {{ and ending with }}""")
    ])
    
    messages = email_prompt.format_messages(analysis=analysis)
    
    print("✉️  Generating email JSON...")
    response = llm.invoke(messages)
    
    # Parse and validate JSON with aggressive cleaning
    try:
        content = response.content.strip()
        
        # Remove all possible markdown formatting
        # Remove leading code block markers
        while content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:].strip()
            elif content.startswith("```"):
                content = content[3:].strip()
        
        # Remove trailing code block markers
        while content.endswith("```"):
            content = content[:-3].strip()
        
        # Remove any "Response content:" prefix if present
        if "Response content:" in content:
            content = content.split("Response content:", 1)[1].strip()
        
        # Find the actual JSON object (starts with { and ends with })
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No valid JSON object found in response")
        
        content = content[start_idx:end_idx + 1]
        
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
