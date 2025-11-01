try:
    from .send_email import send_email
except ImportError:
    from send_email import send_email


def send_agent_startup_email(email: str, hosted_api_url: str, github_repo: str) -> str:
    """
    Send notification email that the agent has started working on a repository.

    Args:
        email: Recipient's email address
        hosted_api_url: URL of the hosted API
        github_repo: GitHub repository URL/name

    Returns:
        message_id of sent email
    """
    email_data = {
        "subject": "🚀 Your Agent Has Started",
        "text": f"""
Hello!

Your agent has successfully started and is now working on your repository.

Repository: {github_repo}
API URL: {hosted_api_url}

The agent is now analyzing your codebase and will begin processing tasks. You'll receive updates as progress is made.

If you have any questions or need to make changes, you can manage your agent through the API at the URL above.

Best regards,
The Recompile Team
        """.strip(),
        "html": f"""
<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0; background: #f9fafb;">
  <!-- Header -->
  <div style="background: #ffffff; border-bottom: 2px solid #e5e5e5; padding: 24px 16px;">
    <div style="max-width: 600px; margin: 0 auto;">
      <h1 style="font-size: 28px; font-weight: 700; margin: 0; color: #1a1a1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
        Recompile
      </h1>
      <p style="font-size: 13px; color: #666; font-weight: 500; margin: 4px 0 0 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
        Agent Startup Notification
      </p>
    </div>
  </div>

  <!-- Main Content Wrapper -->
  <div style="background: #f9fafb; padding: 32px 16px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden;">
      
      <!-- Greeting Section -->
      <div style="padding: 24px; border-bottom: 1px solid #e5e5e5;">
        <p style="margin: 0; font-size: 15px; color: #374151; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
          Hello,
        </p>
        <p style="margin: 12px 0 0 0; font-size: 15px; color: #374151; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
          Your agent has successfully started and is now working on your repository.
        </p>
      </div>

      <!-- Summary Section -->
      <div style="padding: 24px; background: #f0fdf4; border-left: 4px solid #10b981;">
        <p style="margin: 0; font-size: 14px; font-weight: 600; color: #065f46; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
          🚀 Agent is now active
        </p>
        <p style="margin: 8px 0 0 0; font-size: 13px; color: #047857; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
          Our agent is analyzing your codebase and endpoints, and will begin processing tasks. You'll receive a report once it's complete.
        </p>
      </div>

      <!-- Details Section -->
      <div style="padding: 24px;">
        <h2 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600; color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
          Configuration Details
        </h2>
        
        <!-- Repository Card -->
        <div style="margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
          <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
            Repository
          </p>
          <p style="margin: 0; font-size: 14px; color: #1f2937; font-family: 'SF Mono', Monaco, Consolas, monospace; word-break: break-all;">
            {github_repo}
          </p>
        </div>

        <!-- API URL Card -->
        <div style="margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 6px; border: 1px solid #e5e7eb;">
          <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
            API Endpoint
          </p>
          <p style="margin: 0; font-size: 14px; font-family: 'SF Mono', Monaco, Consolas, monospace; word-break: break-all;">
            <a href="{hosted_api_url}" style="color: #3b82f6; text-decoration: none;">{hosted_api_url}</a>
          </p>
        </div>

        <p style="margin: 16px 0 0 0; font-size: 13px; color: #6b7280; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.5;">
          You can manage your agent through the API at the URL above. If you have any questions or need to make changes, feel free to reach out.
        </p>
      </div>

      <!-- Footer -->
      <div style="padding: 20px 24px; background: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="margin: 0; font-size: 12px; color: #9ca3af; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
          Generated by Recompile • Agent Management System
        </p>
      </div>

    </div>
  </div>
</body>
</html>
        """.strip()
    }

    return send_email(email_data, email)


if __name__ == "__main__":
    # SEND A TEST EMAIL to Jake

    class RequestMock:
        email: str
        hosted_api_url: str
        github_repo: str

    request = RequestMock()
    request.email = "benedictnursalim@gmail.com"
    request.github_repo = "https://github.com/JakeRoggenbuck/algoboard"
    request.hosted_api_url = "https://api.algoboard.org"

    message_id = send_agent_startup_email(
        email=request.email,
        hosted_api_url=request.hosted_api_url,
        github_repo=request.github_repo
)
