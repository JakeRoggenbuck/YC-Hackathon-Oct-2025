# Email & Issue Creation Pipeline

Automated API testing analysis, GitHub issue creation, and email notification system powered by AI.

## Overview

This system analyzes API test results using AI, automatically creates GitHub issues for detected problems, and sends detailed email reports to stakeholders.

## Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini to analyze test results and extract errors
- 🐙 **GitHub Integration**: Automatically creates issues via Composio MCP
- ✉️ **Email Notifications**: Sends professional HTML emails with test results
- 🎭 **Mock Mode**: Fast testing without AI calls
- 🔄 **Full Pipeline**: End-to-end automation from test results to notifications

## Files

### Core Pipeline
- **`full_ai_pipeline.py`** - Complete integrated pipeline (analysis → issues → email)
- **`ai_generate_issues.py`** - AI analysis and GitHub issue creation
- **`ai_generate_email.py`** - AI-powered email generation
- **`send_email.py`** - Email sending via Resend API

### Testing & Utilities
- **`test_issues.py`** - End-to-end testing script with mock mode
- **`quick_create_issues.py`** - Standalone issue creation tool
- **`startup_email.py`** - Initial notification when agent starts

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key
RESEND_API_KEY=your_resend_api_key

# Optional for GitHub issue creation
COMPOSIO_MCP_URL=https://mcp.composio.dev/partner/composio/github/mcp?customerId=your_id

# Optional customization
RECIPIENT_EMAIL=recipient@example.com
TARGET_REPO=owner/repo-name
CREATE_GITHUB_ISSUES=true
GEMINI_MODEL=gemini-2.5-flash
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `langchain-google-genai` - AI analysis
- `langchain-mcp-adapters` - GitHub MCP integration
- `resend` - Email sending
- `python-dotenv` - Environment variables

### 3. GitHub Authentication (Optional)

For GitHub issue creation:

```bash
composio login
composio add github
```

## Usage

### Full Pipeline (Recommended)

Run the complete pipeline with analysis, GitHub issues, and email:

```python
from full_ai_pipeline import run_full_pipeline

result = run_full_pipeline(
    test_results="your test results string",
    recipient_email="recipient@example.com",
    target_repo="owner/repo-name",  # Optional
    create_github_issues=True        # Optional
)
```

Or run directly:

```bash
python full_ai_pipeline.py
```

### Test End-to-End (Fast Mode)

Test the complete flow with mock data:

```bash
python test_issues.py
```

**Configuration** (edit top of `test_issues.py`):
```python
TARGET_REPO = "owner/repo-name"
CREATE_ISSUES = True
USE_MOCK_ANALYSIS = True  # Fast testing without AI
```

### Individual Components

**Just create GitHub issues:**
```bash
python quick_create_issues.py test_results.txt
```

**Just send email:**
```python
from ai_generate_email import analyze_api_tests, generate_email_json
from send_email import send_email

analysis = analyze_api_tests(test_results)
email_data = generate_email_json(analysis["analysis"])
send_email(email_data, "recipient@example.com")
```

## How It Works

### 1. AI Analysis

The system uses Google Gemini to:
- Extract all errors from test results
- Identify error codes, causes, and impacts
- Generate actionable fix recommendations
- Structure issues for GitHub

### 2. GitHub Issue Creation

Via Composio MCP, the system:
- Connects to GitHub API
- Creates issues with detailed descriptions
- Assigns appropriate labels
- Returns issue URLs

### 3. Email Generation

Generates professional emails with:
- Clean HTML formatting with Recompile branding
- Error summaries with status codes
- File locations and stack traces
- Actionable fix steps
- Plain text fallback

## Pipeline Modes

### Full Pipeline Mode
```python
run_full_pipeline(
    test_results=results,
    recipient_email="dev@example.com",
    target_repo="owner/repo",
    create_github_issues=True
)
```
**Steps:**
1. Analyze test results with AI
2. Create GitHub issues
3. Generate email report
4. Send email notification

### Email Only Mode
```python
run_email_pipeline(
    test_results=results,
    recipient_email="dev@example.com"
)
```
**Steps:**
1. Analyze test results with AI
2. Generate email report
3. Send email notification

### Analysis Only Mode
```python
from ai_generate_issues import analyze_api_tests

result = analyze_api_tests(test_results)
issues = result["issues"]
```

## Test Results Format

The system accepts any text format:

```
API Test Results - Failed Tests

1. GET /api/users/stats?user_id=123
   Status: 500 Internal Server Error
   Error: ZeroDivisionError: division by zero
   
2. POST /api/orders
   Status: 500 Internal Server Error
   Error: KeyError: 'discount_code' not found
```

## Configuration Options

### Mock Mode (Fast Testing)

In `test_issues.py`, set:
```python
USE_MOCK_ANALYSIS = True
```

Benefits:
- Instant results (no AI API calls)
- Pre-defined test issues
- Perfect for testing GitHub integration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | - | Google Gemini API key |
| `RESEND_API_KEY` | Yes | - | Resend email API key |
| `COMPOSIO_MCP_URL` | No | - | Composio MCP endpoint |
| `RECIPIENT_EMAIL` | No | - | Default email recipient |
| `TARGET_REPO` | No | - | Default GitHub repo |
| `CREATE_GITHUB_ISSUES` | No | `true` | Enable issue creation |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | AI model |

## Troubleshooting

### GitHub Issues Not Creating

1. Check authentication:
   ```bash
   composio add github
   ```

2. Verify `COMPOSIO_MCP_URL` is set

3. Check repo permissions

### Email Not Sending

1. Verify `RESEND_API_KEY` is valid
2. Check `RECIPIENT_EMAIL` format
3. Review Resend dashboard for errors

### AI Analysis Failing

1. Verify `GOOGLE_API_KEY` is set
2. Check API quotas/limits
3. Try using mock mode for testing

## Example Output

```
======================================================================
🚀 RECOMPILE FULL AI PIPELINE
======================================================================

📂 Step 1: Processing test results...
   ✅ Received 9750 characters

🔍 Step 2: Analyzing API test results with Gemini...
   ✅ Analysis complete (5234 chars)
   ✅ Detected 3 issues

🐙 Step 3: Creating GitHub issues in owner/repo...
   ✅ Created 3 issues
      🔗 API returns 500 on empty email: https://github.com/...
      🔗 Missing validation on API URL: https://github.com/...
      🔗 SQL Injection vulnerability: https://github.com/...

✉️  Step 4: Generating email JSON...
   ✅ Generated email:
      Subject: API Test Report: 3 critical errors found in /api/testing_agent
      Text: 1234 chars
      HTML: 5678 chars

📤 Step 5: Sending email to dev@example.com...
   ✅ Sent! Message ID: abc123

======================================================================
🎉 PIPELINE COMPLETE!
======================================================================
```

## Contributing

When adding new features:
1. Update relevant `.py` files
2. Add tests to `test_issues.py`
3. Update this README
4. Test in both mock and real modes

## Support

For issues or questions, create a GitHub issue in the repository.
