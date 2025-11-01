"""
Complete pipeline: analyze -> create issues -> generate email -> send
Chains AI analysis, GitHub issue creation, email generation, and email sending together.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from ai_generate_email import generate_email_json, read_file
from ai_generate_issues import analyze_api_tests
from send_email import send_email
from startup_email import send_agent_startup_email

# Load environment variables
load_dotenv()


def run_ai_pipeline(test_results: str, recipient_email: str, target_repo: str = None, create_github_issues: bool = True):
    """
    Complete pipeline:
    1. Process test results (accepts JSON, text, or any string)
    2. Analyze with AI and detect issues
    3. Create GitHub issues (if enabled and target_repo provided)
    4. Generate email JSON
    5. Send email
    
    Args:
        test_results: String containing test results (can be JSON, plain text, or any format)
        recipient_email: Email address to send the results to
        target_repo: Target GitHub repository in "owner/repo" format (optional)
        create_github_issues: Whether to create GitHub issues (default: True)
    """
    print("=" * 70)
    print("🚀 RECOMPILE FULL AI PIPELINE")
    print("=" * 70)
    print()
    
    # Step 1: Process test results
    print("📂 Step 1: Processing test results...")
    print(f"   ✅ Received {len(test_results)} characters")
    print()
    
    # Step 2: Analyze with AI and detect issues
    print("🔍 Step 2: Analyzing API test results with Gemini...")
    
    # Set up COMPOSIO_MCP_URL before analysis if we want to create issues
    if create_github_issues and target_repo:
        # Make sure COMPOSIO_MCP_URL is set for analyze_api_tests to create issues
        if not os.getenv("COMPOSIO_MCP_URL"):
            print("   ⚠️  Warning: COMPOSIO_MCP_URL not set, issues won't be created")
    
    # Pass target_repo to analyze_api_tests so it can set repo BEFORE creating issues
    analysis_result = analyze_api_tests(test_results, target_repo=target_repo if create_github_issues else None)
    print(f"   ✅ Analysis complete ({len(analysis_result['analysis'])} chars)")
    
    issues = analysis_result.get("issues", [])
    print(f"   ✅ Detected {len(issues)} issues")
    
    print()
    
    # Step 3: Create GitHub issues (if enabled)
    github_results = None
    if create_github_issues and target_repo and issues:
        print(f"🐙 Step 3: Creating GitHub issues in {target_repo}...")
        
        # Update all issues with the target repo
        for issue in issues:
            issue["repo"] = target_repo
        
        issue_results = analysis_result.get("issue_results", [])
        if issue_results:
            success_count = sum(1 for _, resp, err in issue_results if resp and not err)
            failed_count = sum(1 for _, resp, err in issue_results if err)
            
            print(f"   ✅ Created {success_count} issues")
            if failed_count > 0:
                print(f"   ⚠️  {failed_count} issues failed")
            
            # Show created issue URLs
            for spec, response, error in issue_results:
                if response and not error:
                    url = None
                    if hasattr(response, 'html_url'):
                        url = response.html_url
                    elif isinstance(response, dict) and 'html_url' in response:
                        url = response['html_url']
                    
                    if url:
                        print(f"      🔗 {spec.get('title', 'Issue')}: {url}")
            
            github_results = {
                "success": success_count,
                "failed": failed_count,
                "total": len(issue_results)
            }
        else:
            print("   ⚠️  No issue results available (check COMPOSIO_MCP_URL)")
        print()
    elif create_github_issues and not target_repo:
        print("⚠️  Step 3: Skipped GitHub issue creation (no target_repo provided)")
        print()
    elif create_github_issues and not issues:
        print("✨ Step 3: No issues to create - all tests passed!")
        print()
    else:
        print("⏭️  Step 3: GitHub issue creation disabled")
        print()
    
    # Step 4: Generate email JSON
    print("✉️  Step 4: Generating email JSON...")
    email_data = generate_email_json(analysis=analysis_result["analysis"])
    print(f"   ✅ Generated email:")
    print(f"      Subject: {email_data['subject']}")
    print(f"      Text: {len(email_data['text'])} chars")
    print(f"      HTML: {len(email_data['html'])} chars")
    print()
    
    # Step 5: Send email
    print(f"📤 Step 5: Sending email to {recipient_email}...")
    message_id = send_email(email_data, recipient_email)
    print(f"   ✅ Sent! Message ID: {message_id}")
    print()
    
    print("=" * 70)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 70)
    
    result = {
        "message_id": message_id,
        "subject": email_data["subject"],
        "recipient": recipient_email,
        "issues_detected": len(issues),
    }
    
    if github_results:
        result["github_issues"] = github_results
    
    return result


def main():
    """Run the complete pipeline."""
    script_dir = Path(__file__).parent
    test_results_path = str(script_dir / "test_results.txt")
    recipient_email = os.getenv("RECIPIENT_EMAIL", "benedictnursalim@gmail.com")
    target_repo = os.getenv("TARGET_REPO", "JakeRoggenbuck/YC-Hackathon-Oct-2025")
    create_issues = os.getenv("CREATE_GITHUB_ISSUES", "true").lower() == "true"

    # Read the test results file
    test_results = read_file(test_results_path)
    result = run_ai_pipeline(
        test_results=test_results,
        recipient_email=recipient_email,
        target_repo=target_repo,
        create_github_issues=create_issues
    )

    print("\n📊 Summary:")
    print(f"   Subject: {result['subject']}")
    print(f"   To: {result['recipient']}")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Issues Detected: {result['issues_detected']}")
    if 'github_issues' in result:
        gh = result['github_issues']
        print(f"   GitHub Issues Created: {gh['success']}/{gh['total']}")


if __name__ == "__main__":
    main()
