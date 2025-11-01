"""
Complete email pipeline: generate -> validate -> send
Chains generate_email.py and send_email.py together.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from generate_email import analyze_api_tests, generate_email_json, read_file
from send_email import send_email

# Load environment variables
load_dotenv()


def run_pipeline(test_results_path: str, recipient_email: str):
    """
    Complete pipeline:
    1. Read test results
    2. Analyze with AI
    3. Generate email JSON
    4. Validate JSON
    5. Send email
    """
    print("=" * 60)
    print("🚀 RECOMPILE EMAIL PIPELINE")
    print("=" * 60)
    print()
    
    # Step 1: Read test results
    print("📂 Step 1: Reading test results...")
    test_results = read_file(test_results_path)
    print(f"   ✅ Read {len(test_results)} characters")
    print()
    
    # Step 2: Analyze with AI
    print("🔍 Step 2: Analyzing API test results with Gemini...")
    analysis_result = analyze_api_tests(test_results)
    print(f"   ✅ Analysis complete ({len(analysis_result['analysis'])} chars)")
    print()
    
    # Step 3: Generate email JSON
    print("✉️  Step 3: Generating email JSON...")
    email_data = generate_email_json(analysis=analysis_result["analysis"])
    print(f"   ✅ Generated email:")
    print(f"      Subject: {email_data['subject']}")
    print(f"      Text: {len(email_data['text'])} chars")
    print(f"      HTML: {len(email_data['html'])} chars")
    print()
    
    # Step 4: Send email
    print(f"📤 Step 4: Sending email to {recipient_email}...")
    message_id = send_email(email_data, recipient_email)
    print(f"   ✅ Sent! Message ID: {message_id}")
    print()
    
    print("=" * 60)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 60)
    
    return {
        "message_id": message_id,
        "subject": email_data["subject"],
        "recipient": recipient_email
    }


def main():
    """Run the complete pipeline."""
    script_dir = Path(__file__).parent
    test_results_path = str(script_dir / "test_results.txt")
    recipient_email = os.getenv("RECIPIENT_EMAIL", "benedictnursalim@gmail.com")
    
    result = run_pipeline(test_results_path, recipient_email)
    
    print("\n📊 Summary:")
    print(f"   Subject: {result['subject']}")
    print(f"   To: {result['recipient']}")
    print(f"   Message ID: {result['message_id']}")


if __name__ == "__main__":
    main()
