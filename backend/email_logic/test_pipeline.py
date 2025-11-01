#!/usr/bin/env python3
"""
Quick test script to verify the full pipeline creates GitHub issues correctly.
This uses a simplified test case to quickly validate the fix.
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from ai_pipeline import run_ai_pipeline
from startup_email import send_agent_startup_email
# Load environment variables
load_dotenv()


# Sample test results (simplified)
# TEST_RESULTS = """
# === API Test Results ===
# Test: POST /api/testing_agent
# Status: 500 Internal Server Error
# Error: AttributeError: 'NoneType' object has no attribute 'strip'
# Location: Line 42 in api_handler.py

# Test: GET /api/health
# Status: 200 OK
# Response: {"status": "healthy"}

# Test: POST /api/submit
# Status: 400 Bad Request
# Error: Missing required field 'email'
# """

# Read test results from file
script_dir = Path(__file__).parent
test_results_path = script_dir / "test_results.txt"

if not test_results_path.exists():
    print(f"❌ ERROR: test_results.txt not found at {test_results_path}")
    exit(1)

with open(test_results_path, 'r') as f:
    TEST_RESULTS = f.read()

print(f"📄 Loaded test results from {test_results_path.name} ({len(TEST_RESULTS)} characters)")
print()


# Configuration
TARGET_REPO = "JakeRoggenbuck/YC-Hackathon-Oct-2025"  # Change this to your test repo
RECIPIENT_EMAIL = "benedictnursalim@gmail.com"

async def main():
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
        send_agent_startup_email(
            email=RECIPIENT_EMAIL,
            hosted_api_url="https://your-hosted-api-url.com",
            github_repo=TARGET_REPO
        )
        await run_ai_pipeline(
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
    asyncio.run(main())
