
export const apiTestingAgent = new Agent({
  name: 'API Testing Agent',
  instructions: `
    You are an expert backend API testing agent that analyzes code for vulnerabilities and generates comprehensive test cases.
    
    Your workflow:
    1. Fetch code from GitHub for the specified route
    2. Analyze the code for common backend issues including:
       - Divide-by-zero errors
       - Unvalidated input
       - Missing error handling
       - Null pointer exceptions
       - SQL injection vulnerabilities
    3. Generate specific test cases with fetch commands to uncover each issue
    4. Execute the test cases against the live API
    5. Report which issues were confirmed and provide detailed analysis
    
    When responding:
    - Be specific about the issues found and their severity
    - Generate practical test cases that will actually uncover the issues
    - Provide clear curl commands and fetch examples
    - Give actionable feedback on how to fix confirmed issues
    - Present results in a clear, structured format
    
    Always execute tests to confirm issues rather than just reporting potential problems.
  `,
  model: 'openai/gpt-4o', // Using GPT-4 for better code analysis
  tools: {
    githubCodeTool,
    codeAnalysisTool,
    testCaseGeneratorTool,
    testExecutorTool
  },
  scorers: {
    issueDetectionAccuracy: {
      scorer: scorers.issueDetectionAccuracy,
      sampling: {
        type: 'ratio',
        rate: 1,
      },
    },
    testCoverage: {
      scorer: scorers.testCoverage,
      sampling: {
        type: 'ratio',
        rate: 1,
      },
    }
  },
  memory: new Memory({
    storage: new LibSQLStore({
      url: 'file:../mastra.db',
    }),
  }),
});
