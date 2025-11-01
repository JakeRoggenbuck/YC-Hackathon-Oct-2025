import { createTool } from "@mastra/core/tools";
import { z } from "zod";

// Tool to fetch GitHub code for a specific route
export const githubCodeTool = createTool({
  id: "github-code-fetcher",
  description:
    "Fetches source code from a GitHub repository for a specific API route",
  inputSchema: z.object({
    repoOwner: z.string().describe("GitHub repository owner/organization"),
    repoName: z.string().describe("GitHub repository name"),
    filePath: z
      .string()
      .describe(
        "Path to the file containing the route (e.g., src/routes/test.ts)",
      ),
    route: z.string().describe("The API route to analyze (e.g., /test)"),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    code: z.string().nullable().optional(),
    filePath: z.string().optional(),
    route: z.string().optional(),
    analysis: z.string().optional(),
    error: z.string().optional(),
  }),
  execute: async ({ context }) => {
    const { repoOwner, repoName, filePath, route } = context;

    try {
      // Fetch file content from GitHub API
      const url = `https://api.github.com/repos/${repoOwner}/${repoName}/contents/${filePath}`;
      const response = await fetch(url, {
        headers: {
          Accept: "application/vnd.github.v3.raw",
          "User-Agent": "Mastra-API-Testing-Agent",
        },
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.statusText}`);
      }

      const code = await response.text();

      return {
        success: true,
        code,
        filePath,
        route,
        analysis: `Successfully fetched ${code.length} characters of code for route ${route}`,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || "Unknown error",
        code: null,
      };
    }
  },
});

// Tool to analyze code for potential issues
export const codeAnalysisTool = createTool({
  id: "code-analyzer",
  description:
    "Analyzes code for potential backend API issues like divide-by-zero, null references, unhandled errors, etc.",
  inputSchema: z.object({
    code: z.string().describe("The source code to analyze"),
    route: z.string().describe("The API route being analyzed"),
  }),
  outputSchema: z.object({
    route: z.string(),
    issuesFound: z.number(),
    issues: z.array(
      z.object({
        type: z.string(),
        severity: z.string(),
        description: z.string(),
        variable: z.string().optional(),
        code: z.string().optional(),
      }),
    ),
    codeLength: z.number(),
  }),
  execute: async ({ context }) => {
    const { code, route } = context;
    const issues: Array<{
      type: string;
      severity: string;
      description: string;
      variable?: string;
      code?: string;
    }> = [];

    // Detect divide-by-zero vulnerabilities
    const divisionPatterns = [
      /\/\s*([a-zA-Z_][a-zA-Z0-9_]*)/g, // Simple division by variable
      /\/\s*\(([^)]+)\)/g, // Division by expression
      /\/\s*req\.(query|params|body)\.([a-zA-Z0-9_]+)/g, // Division by request params
    ];

    divisionPatterns.forEach((pattern) => {
      const matches = [...code.matchAll(pattern)];
      matches.forEach((match) => {
        const variable = match[1] || match[2];
        if (
          variable &&
          !code.includes(`${variable} === 0`) &&
          !code.includes(`${variable} !== 0`)
        ) {
          issues.push({
            type: "divide-by-zero",
            severity: "high",
            description: `Potential divide-by-zero error with variable: ${variable}`,
            variable,
            code: match[0],
          });
        }
      });
    });

    // Detect unvalidated input
    if (
      code.includes("req.query") ||
      code.includes("req.params") ||
      code.includes("req.body")
    ) {
      const hasValidation =
        code.includes("validate") ||
        code.includes("schema") ||
        code.includes("parseInt") ||
        code.includes("parseFloat");
      if (!hasValidation) {
        issues.push({
          type: "unvalidated-input",
          severity: "medium",
          description: "API route accepts input without apparent validation",
        });
      }
    }

    // Detect missing error handling
    const hasErrorHandling =
      code.includes("try") ||
      code.includes("catch") ||
      code.includes(".catch(");
    if (!hasErrorHandling) {
      issues.push({
        type: "missing-error-handling",
        severity: "medium",
        description: "No error handling detected in route",
      });
    }

    return {
      route,
      issuesFound: issues.length,
      issues,
      codeLength: code.length,
    };
  },
});

// Tool to generate test cases
export const testCaseGeneratorTool = createTool({
  id: "test-case-generator",
  description: "Generates fetch commands to test discovered issues in the API",
  inputSchema: z.object({
    baseUrl: z
      .string()
      .describe("Base URL of the API (e.g., http://localhost:3000)"),
    route: z.string().describe("The API route to test"),
    issues: z.array(z.any()).describe("Array of issues found in the code"),
  }),
  outputSchema: z.object({
    testCasesGenerated: z.number(),
    testCases: z.array(z.any()),
  }),
  execute: async ({ context }) => {
    const { baseUrl, route, issues } = context;
    const testCases: Array<{
      id: string;
      name: string;
      issue: string;
      severity: string;
      fetchCommand: {
        url: string;
        method: string;
        params: Record<string, string>;
        expectedBehavior: string;
      };
      curlCommand: string;
    }> = [];

    issues.forEach((issue: any, index: number) => {
      switch (issue.type) {
        case "divide-by-zero":
          // Generate test cases for divide by zero
          testCases.push({
            id: `test-${index + 1}`,
            name: `Divide by Zero Test - ${issue.variable}`,
            issue: issue.type,
            severity: issue.severity,
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { [issue.variable]: "0" },
              expectedBehavior:
                "Should return 500 error or handle division by zero gracefully",
            },
            curlCommand: `curl "${baseUrl}${route}?${issue.variable}=0"`,
          });

          // Test with very small number
          testCases.push({
            id: `test-${index + 1}b`,
            name: `Divide by Very Small Number - ${issue.variable}`,
            issue: issue.type,
            severity: issue.severity,
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { [issue.variable]: "0.0000001" },
              expectedBehavior: "Should handle very small divisors",
            },
            curlCommand: `curl "${baseUrl}${route}?${issue.variable}=0.0000001"`,
          });
          break;

        case "unvalidated-input":
          // Test with malformed input
          testCases.push({
            id: `test-${index + 1}`,
            name: "Invalid Input Type Test",
            issue: issue.type,
            severity: issue.severity,
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { input: "not-a-number" },
              expectedBehavior: "Should validate input and return 400 error",
            },
            curlCommand: `curl "${baseUrl}${route}?input=not-a-number"`,
          });
          break;

        case "missing-error-handling":
          // Test error scenarios
          testCases.push({
            id: `test-${index + 1}`,
            name: "Error Handling Test",
            issue: issue.type,
            severity: issue.severity,
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { trigger: "error" },
              expectedBehavior: "Should handle errors gracefully",
            },
            curlCommand: `curl "${baseUrl}${route}?trigger=error"`,
          });
          break;
      }
    });

    return {
      testCasesGenerated: testCases.length,
      testCases,
    };
  },
});

// Tool to execute test cases
export const testExecutorTool = createTool({
  id: "test-executor",
  description:
    "Executes the generated test cases against the API and reports results",
  inputSchema: z.object({
    testCases: z.array(z.any()).describe("Array of test cases to execute"),
  }),
  outputSchema: z.object({
    summary: z.object({
      totalTests: z.number(),
      passed: z.number(),
      failed: z.number(),
      issuesConfirmed: z.number(),
    }),
    results: z.array(z.any()),
  }),
  execute: async ({ context }) => {
    const { testCases } = context;
    const results: Array<{
      testId: string;
      testName: string;
      issue?: string;
      severity?: string;
      passed: boolean;
      status?: number;
      statusText?: string;
      responseTime?: number;
      responseBody?: any;
      analysis: string;
      error?: string;
    }> = [];

    for (const testCase of testCases) {
      try {
        const { url, method, params } = testCase.fetchCommand;
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = `${url}?${queryString}`;

        const startTime = Date.now();
        const response = await fetch(fullUrl, { method });
        const endTime = Date.now();

        let responseBody;
        const contentType = response.headers.get("content-type");

        if (contentType && contentType.includes("application/json")) {
          responseBody = await response.json();
        } else {
          responseBody = await response.text();
        }

        const testResult = {
          testId: testCase.id,
          testName: testCase.name,
          issue: testCase.issue,
          severity: testCase.severity,
          passed: false,
          status: response.status,
          statusText: response.statusText,
          responseTime: endTime - startTime,
          responseBody,
          analysis: "",
        };

        // Analyze if the issue was confirmed
        if (testCase.issue === "divide-by-zero") {
          if (
            response.status === 500 ||
            (responseBody &&
              typeof responseBody === "string" &&
              (responseBody.includes("division by zero") ||
                responseBody.includes("Infinity") ||
                responseBody.includes("NaN")))
          ) {
            testResult.passed = false;
            testResult.analysis =
              "🔴 ISSUE CONFIRMED: Divide by zero error detected!";
          } else if (
            response.status === 400 &&
            responseBody &&
            (responseBody.error || typeof responseBody === "object")
          ) {
            testResult.passed = true;
            testResult.analysis =
              "✅ PASS: API properly validates and rejects zero divisor";
          } else {
            testResult.passed = true;
            testResult.analysis =
              "✅ PASS: API handles division by zero gracefully";
          }
        } else if (testCase.issue === "unvalidated-input") {
          if (response.status === 400) {
            testResult.passed = true;
            testResult.analysis = "✅ PASS: API validates input properly";
          } else {
            testResult.passed = false;
            testResult.analysis =
              "🔴 ISSUE CONFIRMED: API accepts invalid input";
          }
        } else {
          testResult.passed = response.status < 500;
          testResult.analysis =
            response.status < 500
              ? "✅ PASS: No server error"
              : "🔴 ISSUE CONFIRMED: Server error occurred";
        }

        results.push(testResult);
      } catch (error: any) {
        results.push({
          testId: testCase.id,
          testName: testCase.name,
          passed: false,
          error: error.message || "Unknown error",
          analysis: "🔴 ERROR: Test execution failed",
        });
      }
    }

    const summary = {
      totalTests: results.length,
      passed: results.filter((r) => r.passed).length,
      failed: results.filter((r) => !r.passed).length,
      issuesConfirmed: results.filter(
        (r) => !r.passed && r.analysis.includes("CONFIRMED"),
      ).length,
    };

    return {
      summary,
      results,
    };
  },
});
