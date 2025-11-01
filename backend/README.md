# Start Agent API Documentation

## Endpoint

**POST** `/start-agent`

Starts an agent with the provided configuration.

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `hosted_api_url` | string | Yes | URL of the hosted API |
| `github_repo` | string | Yes | GitHub repository URL |

## Response

```json
{
  "status": "success",
  "message": "Agent started successfully",
  "data": {
    "email": "user@example.com",
    "hosted_api_url": "https://api.example.com",
    "github_repo": "https://github.com/user/repo"
  }
}
```

## TypeScript Example

### Installation

```bash
npm install axios
# or
npm install node-fetch
```

### Using Axios

```typescript
import axios from 'axios';

interface StartAgentRequest {
  email: string;
  hosted_api_url: string;
  github_repo: string;
}

interface StartAgentResponse {
  status: string;
  message: string;
  data: StartAgentRequest;
}

async function startAgent(config: StartAgentRequest): Promise<StartAgentResponse> {
  try {
    const response = await axios.post<StartAgentResponse>(
      'http://localhost:8000/start-agent',
      config
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`API Error: ${error.response?.data?.detail || error.message}`);
    }
    throw error;
  }
}

// Usage
const result = await startAgent({
  email: 'developer@example.com',
  hosted_api_url: 'https://api.myservice.com',
  github_repo: 'https://github.com/myorg/myrepo'
});

console.log(result);
```

### Using Fetch

```typescript
interface StartAgentRequest {
  email: string;
  hosted_api_url: string;
  github_repo: string;
}

interface StartAgentResponse {
  status: string;
  message: string;
  data: StartAgentRequest;
}

async function startAgent(config: StartAgentRequest): Promise<StartAgentResponse> {
  const response = await fetch('http://localhost:8000/start-agent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error: ${error.detail || response.statusText}`);
  }

  return response.json();
}

// Usage
const result = await startAgent({
  email: 'developer@example.com',
  hosted_api_url: 'https://api.myservice.com',
  github_repo: 'https://github.com/myorg/myrepo'
});

console.log(result);
```

## Error Handling

The API returns errors in the following format:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### TypeScript Error Handling Example

```typescript
try {
  const result = await startAgent({
    email: 'invalid-email',
    hosted_api_url: 'https://api.example.com',
    github_repo: 'https://github.com/user/repo'
  });
} catch (error) {
  console.error('Failed to start agent:', error);
}
```

## cURL Example

```bash
curl -X POST http://localhost:8000/start-agent \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "hosted_api_url": "https://api.myservice.com",
    "github_repo": "https://github.com/myorg/myrepo"
  }'
```

## Status Codes

- `200` - Success
- `422` - Validation Error (invalid email, missing fields, etc.)
- `500` - Internal Server Error
