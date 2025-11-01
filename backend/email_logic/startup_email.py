from email_logic.send_email import send_email


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
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Your Agent Has Started</h1>
        </div>
        <div class="content">
            <p>Hello!</p>
            <p>Your agent has successfully started and is now working on your repository.</p>

            <div class="info-box">
                <p><strong>Repository:</strong><br><code>{github_repo}</code></p>
                <p><strong>API URL:</strong><br><a href="{hosted_api_url}">{hosted_api_url}</a></p>
            </div>

            <p>The agent is now analyzing your codebase and will begin processing tasks. You'll receive updates as progress is made.</p>

            <p>If you have any questions or need to make changes, you can manage your agent through the API at the URL above.</p>

            <p>Best regards,<br><strong>The Recompile Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message from your Recompile agent service.</p>
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
