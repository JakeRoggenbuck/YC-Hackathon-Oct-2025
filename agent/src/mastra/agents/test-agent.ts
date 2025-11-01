import { Agent } from "@mastra/core/agent";
import { Memory } from "@mastra/memory";
import { LibSQLStore } from "@mastra/libsql";
import {
  githubCodeTool,
  githubRepositoryExplorerTool,
  codeAnalysisTool,
  testCaseGeneratorTool,
  testExecutorTool,
} from "../tools/api-testing-tool";
import { scorers } from "../scorers/api-testing-scorer";

export const apiTestingAgent = new Agent({
  name: "API Testing Agent",
  instructions: `
    You are an expert backend API testing agent that analyzes code for vulnerabilities and generates comprehensive test cases.
    
    Your workflow:
    1. If you don't know the exact file path in the repository, use github-repository-explorer to explore the repository structure and find route files
    2. Fetch code from GitHub for the specified route using github-code-fetcher
       - If the repository is private, you may need a GitHub token (ask the user if you encounter 403/404 errors)
       - If file not found, use github-repository-explorer to find the correct path
    3. Analyze the code for common backend issues including:
       - Divide-by-zero errors
       - Unvalidated input
       - Missing error handling
       - Null pointer exceptions
       - SQL injection vulnerabilities
    4. Generate specific test cases with fetch commands to uncover each issue
    5. Execute the test cases against the live API
    6. Report which issues were confirmed and provide detailed analysis
    
    When responding:
    - If you encounter "Not Found" errors, use github-repository-explorer to explore the repository structure first
    - Be specific about the issues found and their severity
    - Generate practical test cases that will actually uncover the issues
    - Provide clear curl commands and fetch examples
    - Give actionable feedback on how to fix confirmed issues
    - Present results in a clear, structured format
    
    Always execute tests to confirm issues rather than just reporting potential problems.
  `,
  model: "openai/gpt-4o", // Using GPT-4 for better code analysis
  tools: {
    githubCodeTool,
    githubRepositoryExplorerTool,
    codeAnalysisTool,
    testCaseGeneratorTool,
    testExecutorTool,
  },
  scorers: {
    issueDetectionAccuracy: {
      scorer: scorers.issueDetectionAccuracyScorer,
      sampling: {
        type: "ratio",
        rate: 1,
      },
    },
    testCoverage: {
      scorer: scorers.testCoverageScorer,
      sampling: {
        type: "ratio",
        rate: 1,
      },
    },
  },
  memory: new Memory({
    storage: new LibSQLStore({
      url: "file:../mastra.db",
    }),
  }),
});
