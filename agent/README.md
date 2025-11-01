# Agent - API Testing Agents

Mastra-based TypeScript agents that perform automated API testing, code analysis, and vulnerability detection.

## Overview

Intelligent agents that analyze FastAPI backends by scanning GitHub repositories, detecting code issues, generating test cases, and executing tests against live APIs. Results are scored and evaluated for accuracy.

## Tech Stack

- **Mastra** framework for agent orchestration
- **TypeScript/Node.js** (Node >=20.9.0)
- **LibSQL** for storage and observability
- **Pino** for logging

## Getting Started

```bash
npm install
npm run dev    # Development mode
npm run build  # Build for production
npm start      # Production mode
```

## Project Structure

```
agent/
├── src/mastra/
│   ├── agents/          # Agent definitions
│   │   ├── test-agent.ts        # API testing agent
│   │   └── weather-agent.ts     # Example weather agent
│   ├── tools/           # Agent tools
│   │   ├── api-testing-tool.ts  # GitHub code fetching, analysis, testing
│   │   └── weather-tool.ts
│   ├── workflows/       # Agent workflows
│   ├── scorers/         # Evaluation scorers
│   └── index.ts         # Mastra configuration
```

## Agents

### API Testing Agent (`apiTestingAgent`)

Performs comprehensive backend API testing:

1. **Repository Exploration**: Navigates GitHub repos to find route implementations
2. **Code Analysis**: Detects vulnerabilities (divide-by-zero, unvalidated input, missing error handling, etc.)
3. **Test Generation**: Creates specific test cases for detected issues
4. **Test Execution**: Runs tests against live APIs to confirm issues
5. **Reporting**: Provides detailed analysis and remediation suggestions

### Tools

- `githubCodeTool`: Fetches code from GitHub repositories
- `githubRepositoryExplorerTool`: Explores repository structure
- `codeAnalysisTool`: Analyzes code for common backend issues
- `testCaseGeneratorTool`: Generates test cases from detected issues
- `testExecutorTool`: Executes tests against live API endpoints

## Environment Variables

Required for agent operation:

```
OPENAI_API_KEY=      # OpenAI API key for agent LLM
GITHUB_TOKEN=        # GitHub PAT (public repos only)
```

## Scorers

Evaluation metrics for agent performance:

- `issueDetectionAccuracyScorer`: Measures accuracy of issue detection
- `testCoverageScorer`: Evaluates test case coverage
