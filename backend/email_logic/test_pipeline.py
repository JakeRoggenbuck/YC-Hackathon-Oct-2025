#!/usr/bin/env python3
"""
Quick test script to verify the full pipeline creates GitHub issues correctly.
This uses a simplified test case to quickly validate the fix.
"""

import os
from dotenv import load_dotenv
from ai_pipeline import run_full_pipeline

# Load environment variables
load_dotenv()


# Sample test results (simplified)
TEST_RESULTS = """
=== API Test Results ===
Test: POST /api/testing_agent
Status: 500 Internal Server Error
Error: AttributeError: 'NoneType' object has no attribute 'strip'
Location: Line 42 in api_handler.py

Test: GET /api/health
Status: 200 OK
Response: {"status": "healthy"}

Test: POST /api/submit
Status: 400 Bad Request
Error: Missing required field 'email'
"""

# Configuration
TARGET_REPO = "JakeRoggenbuck/YC-Hackathon-Oct-2025"  # Change this to your test repo
RECIPIENT_EMAIL = "benedictnursalim@gmail.com"

def main():
    print("=" * 70)
    print("QUICK PIPELINE TEST")
    print("=" * 70)
    print(f"Target Repo: {TARGET_REPO}")
    print(f"Create Issues: True")
    print()
    
    # Check environment
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not set")
        return
    
    if not os.getenv("COMPOSIO_MCP_URL"):
        print("❌ ERROR: COMPOSIO_MCP_URL not set - issues won't be created!")
        return
    
    print("✅ Environment configured correctly")
    print()
    
    # Run pipeline
    try:
        run_full_pipeline(
            test_results=TEST_RESULTS,
            recipient_email=RECIPIENT_EMAIL,
            target_repo=TARGET_REPO,
            create_github_issues=True
        )
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
