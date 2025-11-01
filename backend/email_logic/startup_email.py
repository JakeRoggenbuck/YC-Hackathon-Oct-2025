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
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin-top: 20px; }}
        .info-box {{ background-color: #e8f5e9; border-left: 4px solid #4CAF50; padding: 15px; margin: 15px 0; }}
        .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
        a {{ color: #4CAF50; text-decoration: none; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
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
    request.email = "me@jr0.org"
    request.github_repo = "https://github.com/JakeRoggenbuck/algoboard"
    request.hosted_api_url = "https://api.algoboard.org"

    message_id = send_agent_startup_email(
        email=request.email,
        hosted_api_url=request.hosted_api_url,
        github_repo=request.github_repo
)
