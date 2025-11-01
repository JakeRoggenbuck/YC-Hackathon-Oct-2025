import os
import json
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from agentmail import AgentMail

# Load environment variables from .env
load_dotenv()

# Get API key from environment
AGENTMAIL_API_KEY = os.getenv("AGENTMAIL_API_KEY")
if not AGENTMAIL_API_KEY:
    raise ValueError("AGENTMAIL_API_KEY not found in environment variables. Please set it in .env file.")

client = AgentMail(api_key=AGENTMAIL_API_KEY)


def send_email(email_data: Dict[str, str], recipient_email: str) -> str:
    """
    Send email using AgentMail with validated JSON data.
    
    Args:
        email_data: Dict with keys 'subject', 'text', 'html'
        recipient_email: Email address to send to
        
    Returns:
        message_id of sent email
    """
    # Validate email_data
    required_fields = ["subject", "text", "html"]
    for field in required_fields:
        if field not in email_data:
            raise ValueError(f"Missing required field in email_data: {field}")
    
    print(f"📤 Sending email to {recipient_email}...")
    
    sent_message = client.inboxes.messages.send(
        inbox_id='recompile@agentmail.to',
        to=recipient_email,
        subject=email_data["subject"],
        text=email_data["text"],
        html=email_data["html"]
    )
    
    print(f"✅ Message sent successfully with ID: {sent_message.message_id}")
    return sent_message.message_id


def main():
    """Load email JSON and send it."""
    script_dir = Path(__file__).parent
    email_json_path = script_dir / "email_output.json"
    
    # Load email data
    print(f"📂 Loading email data from: {email_json_path}")
    with open(email_json_path, 'r') as f:
        email_data = json.load(f)
    
    # Send email
    recipient = os.getenv("RECIPIENT_EMAIL", "benedictnursalim@gmail.com")
    message_id = send_email(email_data, recipient)
    
    print(f"\n🎉 Email sent successfully!")
    print(f"Message ID: {message_id}")


if __name__ == "__main__":
    main()