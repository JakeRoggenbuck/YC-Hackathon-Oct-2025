import { createTool } from "@mastra/core/tools";
import { z } from "zod";

// Helper function to create GitHub API headers
const getGitHubHeaders = (token?: string) => {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github.v3.raw",
    "User-Agent": "Mastra-API-Testing-Agent",
  };
  if (token) {
    // GitHub API accepts both "token" and "Bearer" prefixes for personal access tokens
    // Use the token as-is if it already has a prefix, otherwise add "token" prefix
    headers.Authorization = token.startsWith("Bearer ") || token.startsWith("token ")
      ? token
      : `token ${token}`;
  }
  return headers;
};

// Tool to list repository contents
export const githubRepositoryExplorerTool = createTool({
  id: "github-repository-explorer",
  description:
    "Lists the contents of a GitHub repository directory to help find route files. Use this when you don't know the exact file path.",
  inputSchema: z.object({
    repoOwner: z.string().describe("GitHub repository owner/organization"),
    repoName: z.string().describe("GitHub repository name"),
    directoryPath: z
      .string()
      .optional()
      .describe(
        "Directory path to explore (e.g., src/routes). Leave empty for root directory.",
      ),
    githubToken: z
      .string()
      .optional()
      .describe(
        "Optional GitHub personal access token for private repositories",
      ),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    path: z.string().optional(),
    files: z
      .array(
        z.object({
          name: z.string(),
          type: z.string(),
          path: z.string(),
          size: z.number().optional(),
        }),
      )
      .optional(),
    error: z.string().optional(),
    suggestions: z.array(z.string()).optional(),
  }),
  execute: async ({ context }) => {
    const { repoOwner, repoName, directoryPath = "", githubToken } = context;

    try {
      const url = `https://api.github.com/repos/${repoOwner}/${repoName}/contents/${directoryPath}`;
      const response = await fetch(url, {
        headers: getGitHubHeaders(githubToken),
      });

      if (response.status === 404) {
        return {
          success: false,
          error: `Repository or path not found. The repository might be private (requires authentication), the path might be incorrect, or the repository doesn't exist.`,
          suggestions: [
            "Check if the repository name and owner are correct",
            "If the repository is private, provide a GitHub token",
            "Try exploring the root directory first (empty directoryPath)",
          ],
        };
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`GitHub API error (${response.status}): ${errorText}`);
      }

      const contents = await response.json();

      // Handle both single file and directory responses
      const files = Array.isArray(contents)
        ? contents.map((item: any) => ({
            name: item.name,
            type: item.type,
            path: item.path,
            size: item.size,
          }))
        : [
            {
              name: contents.name,
              type: contents.type,
              path: contents.path,
              size: contents.size,
            },
          ];

      // Suggest route-related files
      const suggestions: string[] = [];
      const routeFiles = files.filter(
        (f) =>
          f.type === "file" &&
          (f.name.includes("route") ||
            f.name.includes("api") ||
            f.path.includes("routes") ||
            f.path.includes("api")),
      );
      if (routeFiles.length > 0) {
        suggestions.push(
          `Found potential route files: ${routeFiles.map((f) => f.path).join(", ")}`,
        );
      }

      return {
        success: true,
        path: directoryPath || "/",
        files,
        suggestions,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || "Unknown error",
        suggestions: [
          "Verify repository owner and name are correct",
          "Check if repository is private and requires authentication",
        ],
      };
    }
  },
});

// Tool to fetch GitHub code for a specific route
export const githubCodeTool = createTool({
  id: "github-code-fetcher",
  description:
    "Fetches source code from a GitHub repository for a specific API route. If the file is not found, try using github-repository-explorer to find the correct path.",
  inputSchema: z.object({
    repoOwner: z.string().describe("GitHub repository owner/organization"),
    repoName: z.string().describe("GitHub repository name"),
    filePath: z
      .string()
      .describe(
        "Path to the file containing the route (e.g., src/routes/test.ts)",
      ),
    route: z.string().describe("The API route to analyze (e.g., /test)"),
    githubToken: z
      .string()
      .optional()
      .describe(
        "Optional GitHub personal access token for private repositories",
      ),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    code: z.string().nullable().optional(),
    filePath: z.string().optional(),
    route: z.string().optional(),
    analysis: z.string().optional(),
    error: z.string().optional(),
    suggestions: z.array(z.string()).optional(),
  }),
  execute: async ({ context }) => {
    const { repoOwner, repoName, filePath, route, githubToken } = context;

    try {
      // Fetch file content from GitHub API
      const url = `https://api.github.com/repos/${repoOwner}/${repoName}/contents/${filePath}`;
      const response = await fetch(url, {
        headers: getGitHubHeaders(githubToken),
      });

      if (response.status === 404) {
        // First, check if the repository itself exists by trying to access the root
        try {
          const repoCheckUrl = `https://api.github.com/repos/${repoOwner}/${repoName}`;
          const repoCheckResponse = await fetch(repoCheckUrl, {
            headers: getGitHubHeaders(githubToken),
          });
          
          if (repoCheckResponse.status === 404) {
            return {
              success: false,
              error: `Repository not found: ${repoOwner}/${repoName}`,
              code: null,
              suggestions: [
                "The repository does not exist or the owner/name is incorrect.",
                "Verify the repository owner and name are correct.",
                "If the repository is private, you may need to provide a GitHub token.",
              ],
            };
          }
          
          if (repoCheckResponse.status === 403) {
            return {
              success: false,
              error: `Access forbidden to repository: ${repoOwner}/${repoName}`,
              code: null,
              suggestions: [
                "This repository appears to be private. Provide a GitHub personal access token via the githubToken parameter.",
                "Create a token at: https://github.com/settings/tokens",
              ],
            };
          }
        } catch (repoCheckError) {
          // If repo check fails, continue with file not found error
        }
        
        // Repository exists, but file path is likely incorrect
        return {
          success: false,
          error: `File not found at path: ${filePath}`,
          code: null,
          suggestions: [
            `The file path "${filePath}" was not found in the repository "${repoOwner}/${repoName}".`,
            `The repository exists, so the file path is likely incorrect.`,
            `Use github-repository-explorer tool with repoOwner="${repoOwner}", repoName="${repoName}" to explore the repository structure and find the correct file path.`,
            `Common paths to check: src/routes, app/routes, routes, api, src/api, backend/routes`,
            `You can start by exploring the root directory (empty directoryPath) or try common route directories.`,
          ],
        };
      }

      if (response.status === 403) {
        return {
          success: false,
          error: "Access forbidden. Repository may be private.",
          code: null,
          suggestions: [
            "This repository appears to be private. Provide a GitHub personal access token via the githubToken parameter.",
            "Create a token at: https://github.com/settings/tokens",
          ],
        };
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `GitHub API error (${response.status}): ${response.statusText}. ${errorText}`,
        );
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
        suggestions: [
          "Verify the repository owner, name, and file path are correct",
          "Try using github-repository-explorer to explore the repository structure",
          "If the repository is private, provide a GitHub token",
        ],
      };
    }
  },
});

// Tool to analyze code for potential issues
export const codeAnalysisTool = createTool({
  id: "code-analyzer",
  description:
    "Analyzes code for potential backend API issues. Only detects actual issues in the code - does not infer or assume issues exist. Returns an empty issues array if no issues are found.",
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

    // Detect divide-by-zero vulnerabilities - only in actual mathematical operations
    // Look for patterns like: variable / divisor, number / variable, etc.
    // Exclude string literals, regex patterns, and route paths
    
    // Remove comments and string literals from analysis to avoid false positives
    const codeWithoutStrings = code
      .replace(/\/\/.*$/gm, '') // Remove single-line comments
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove multi-line comments
      .replace(/"[^"]*"/g, '""') // Replace string literals with empty strings
      .replace(/'[^']*'/g, "''"); // Replace single-quoted strings

    // Only match division operations with variables/expressions on both sides
    // Pattern: something / variable (where something is a number, variable, or expression)
    const divisionPatterns = [
      // Match: variable / variable, number / variable, expression / variable
      /([a-zA-Z_][a-zA-Z0-9_]*|\)|\d+)\s*\/\s*([a-zA-Z_][a-zA-Z0-9_]*)/g,
      // Match: something / req.query/params/body.field
      /([a-zA-Z_][a-zA-Z0-9_]*|\)|\d+)\s*\/\s*req\.(query|params|body)\.([a-zA-Z0-9_]+)/g,
    ];

    const foundVariables = new Set<string>();

    divisionPatterns.forEach((pattern) => {
      const matches = [...codeWithoutStrings.matchAll(pattern)];
      matches.forEach((match) => {
        // Get the divisor (right side of division)
        const variable = match[2] || match[3];
        const fullMatch = match[0];
        
        // Skip if this is clearly not a division operation (e.g., route paths, regex)
        if (fullMatch.includes('"/') || fullMatch.includes("'/") || fullMatch.includes('/g')) {
          return;
        }
        
        if (variable && !foundVariables.has(variable)) {
          // Check if there's any validation or check for this variable
          const hasZeroCheck = 
            code.includes(`${variable} === 0`) ||
            code.includes(`${variable} !== 0`) ||
            code.includes(`${variable} == 0`) ||
            code.includes(`${variable} != 0`) ||
            code.includes(`if (${variable}`) ||
            code.includes(`if(${variable}`) ||
            code.includes(`&& ${variable}`) ||
            code.includes(`|| ${variable}`);
          
          // Only flag if no zero check exists and it's not a common safe variable name
          const isLikelyDivisor = !['id', 'type', 'name', 'key', 'value', 'path', 'url', 'route'].includes(variable.toLowerCase());
          
          if (!hasZeroCheck && isLikelyDivisor) {
            foundVariables.add(variable);
            issues.push({
              type: "divide-by-zero",
              severity: "high",
              description: `Potential divide-by-zero error: division by variable "${variable}" without zero check`,
              variable,
              code: fullMatch.trim(),
            });
          }
        }
      });
    });

    // Detect unvalidated input - be more conservative
    // Only flag if there's direct use of user input in operations without validation
    const hasUserInput = 
      code.includes("req.query") || 
      code.includes("req.params") || 
      code.includes("req.body");
    
    if (hasUserInput) {
      // Check for various validation patterns
      const hasValidation =
        code.includes("validate") ||
        code.includes("schema") ||
        code.includes("zod") ||
        code.includes("yup") ||
        code.includes("joi") ||
        code.includes("parseInt") ||
        code.includes("parseFloat") ||
        code.includes("Number(") ||
        code.includes("parseInt(") ||
        code.includes("isNaN") ||
        code.includes("typeof") ||
        code.includes("instanceof");
      
      // Only flag if input is used in potentially dangerous operations without validation
      const hasUnsafeOperations = 
        code.match(/req\.(query|params|body)\.[a-zA-Z0-9_]+/g)?.some(match => {
          const varName = match.split('.').pop();
          return varName && (
            code.includes(`${varName} /`) ||
            code.includes(`/ ${varName}`) ||
            code.includes(`eval(`) ||
            code.includes(`exec(`)
          );
        }) || false;
      
      if (hasUnsafeOperations && !hasValidation) {
        issues.push({
          type: "unvalidated-input",
          severity: "medium",
          description: "User input used in operations without apparent validation",
        });
      }
    }

    // Detect unhandled exceptions (raise/throw statements)
    // Check for raise (Python) or throw (JavaScript/TypeScript) statements
    const raiseThrowPatterns = [
      /\braise\s+[A-Za-z]/g, // Python: raise Exception
      /\braise\s*$/g, // Python: raise (re-raise)
      /\bthrow\s+new\s+Error/g, // JavaScript: throw new Error
      /\bthrow\s+new\s+[A-Z]/g, // JavaScript: throw new Exception
      /\bthrow\s+[A-Za-z]/g, // JavaScript: throw variable
    ];

    const hasRaiseThrow = raiseThrowPatterns.some(pattern => pattern.test(codeWithoutStrings));
    
    if (hasRaiseThrow) {
      // Check if exceptions are within try/catch blocks
      // Simple check: count raise/throw statements and try/catch blocks
      const raiseMatches = codeWithoutStrings.match(/\braise\b/g);
      const throwMatches = codeWithoutStrings.match(/\bthrow\b/g);
      const tryMatches = codeWithoutStrings.match(/\btry\s*{/g) || codeWithoutStrings.match(/\btry\s*:/g);
      const catchMatches = codeWithoutStrings.match(/\bcatch\s*\(/g) || codeWithoutStrings.match(/\bexcept\s*:/g);
      
      const exceptionCount = (raiseMatches?.length || 0) + (throwMatches?.length || 0);
      const tryCount = tryMatches?.length || 0;
      const catchCount = catchMatches?.length || 0;
      
      // Flag if there are more exceptions than catch blocks
      if (exceptionCount > 0 && (tryCount === 0 || catchCount === 0 || exceptionCount > catchCount)) {
        issues.push({
          type: "unhandled-exceptions",
          severity: "high",
          description: `Found ${exceptionCount} raise/throw statement(s) without proper error handling. Exceptions should be caught in try/catch or try/except blocks.`,
        });
      }
    }

    // Detect missing error handling - be more conservative
    // Only flag if there are operations that could throw errors without handling
    const hasAsyncOperations = 
      code.includes("async") || 
      code.includes("await") || 
      code.includes("Promise") ||
      code.includes(".then(") ||
      code.includes("fetch(") ||
      code.includes("axios") ||
      code.includes("database") ||
      code.includes("db.");
    
    const hasErrorHandling =
      code.includes("try") ||
      code.includes("catch") ||
      code.includes(".catch(") ||
      code.includes("except");
    
    // Only flag missing error handling if there are operations that could fail
    if (hasAsyncOperations && !hasErrorHandling) {
      issues.push({
        type: "missing-error-handling",
        severity: "medium",
        description: "Async operations detected without error handling",
      });
    }

    // Detect common Python errors
    const isPythonCode = code.includes("def ") || code.includes("import ") || code.includes("from ") || 
                         code.includes(".py") || code.includes("if __name__") || code.includes("print(");
    
    if (isPythonCode) {
      // 1. KeyError: Dictionary access without .get() or 'in' check
      // Pattern: dict[key] without dict.get(key) or key in dict check
      const dictAccessPattern = /([a-zA-Z_][a-zA-Z0-9_]*)\[([^\]]+)\]/g;
      const dictAccesses = [...codeWithoutStrings.matchAll(dictAccessPattern)];
      const checkedDicts = new Set<string>();
      
      dictAccesses.forEach((match) => {
        const dictName = match[1];
        const key = match[2];
        
        // Skip if it's list indexing (not dict access) - simple heuristic
        if (key.match(/^\d+$/)) {
          return; // Likely list index, not dict key
        }
        
        // Check if this dict is safely accessed with .get() or 'in' check
        const hasSafeAccess = 
          code.includes(`${dictName}.get(`) ||
          code.includes(`if ${key} in ${dictName}`) ||
          code.includes(`if "${key}" in ${dictName}`) ||
          code.includes(`if '${key}' in ${dictName}`) ||
          code.includes(`if ${dictName}.get(`) ||
          checkedDicts.has(dictName);
        
        if (!hasSafeAccess && !checkedDicts.has(dictName)) {
          checkedDicts.add(dictName);
          issues.push({
            type: "python-keyerror",
            severity: "medium",
            description: `Dictionary access "${dictName}[${key}]" may raise KeyError if key doesn't exist. Consider using "${dictName}.get(${key})" or check with "in" operator.`,
            variable: dictName,
            code: match[0],
          });
        }
      });

      // 2. IndexError: List access without bounds checking
      // Pattern: list[index] where index could be out of range
      const listAccessPattern = /([a-zA-Z_][a-zA-Z0-9_]*)\[([a-zA-Z_][a-zA-Z0-9_]*)\]/g;
      const listAccesses = [...codeWithoutStrings.matchAll(listAccessPattern)];
      const checkedLists = new Set<string>();
      
      listAccesses.forEach((match) => {
        const listName = match[1];
        const indexVar = match[2];
        
        // Skip if index is a literal number (probably safe)
        if (indexVar.match(/^\d+$/)) {
          return;
        }
        
        // Check if there's bounds checking
        const hasBoundsCheck = 
          code.includes(`len(${listName})`) ||
          code.includes(`if ${indexVar} < len(${listName})`) ||
          code.includes(`if ${indexVar} < ${listName}.__len__`) ||
          code.includes(`try:`) ||
          checkedLists.has(listName);
        
        if (!hasBoundsCheck && !checkedLists.has(listName)) {
          checkedLists.add(listName);
          issues.push({
            type: "python-indexerror",
            severity: "medium",
            description: `List access "${listName}[${indexVar}]" may raise IndexError if index is out of range. Consider checking bounds with len() or use try/except.`,
            variable: listName,
            code: match[0],
          });
        }
      });

      // 3. AttributeError: Object attribute access without None check or hasattr()
      // Pattern: obj.attr where obj could be None
      const attrAccessPattern = /([a-zA-Z_][a-zA-Z0-9_]*)\\.([a-zA-Z_][a-zA-Z0-9_]*)/g;
      const attrAccesses = [...codeWithoutStrings.matchAll(attrAccessPattern)];
      const checkedObjs = new Set<string>();
      
      attrAccesses.forEach((match) => {
        const objName = match[1];
        const attrName = match[2];
        
        // Skip common safe patterns
        if (['self', 'cls', '__class__', '__name__'].includes(objName) || 
            ['__init__', '__str__', '__repr__'].includes(attrName)) {
          return;
        }
        
        // Check if there's None check or hasattr()
        const hasSafeAccess = 
          code.includes(`if ${objName} is not None`) ||
          code.includes(`if ${objName} != None`) ||
          code.includes(`hasattr(${objName}`) ||
          code.includes(`getattr(${objName}`) ||
          code.includes(`if ${objName}:`) ||
          checkedObjs.has(objName);
        
        if (!hasSafeAccess && !checkedObjs.has(objName)) {
          checkedObjs.add(objName);
          issues.push({
            type: "python-attributeerror",
            severity: "medium",
            description: `Attribute access "${objName}.${attrName}" may raise AttributeError if ${objName} is None or doesn't have the attribute. Consider checking with "if ${objName} is not None" or using hasattr().`,
            variable: objName,
            code: match[0],
          });
        }
      });

      // 4. FileNotFoundError: File operations without try/except
      const fileOperations = [
        /open\s*\(/g,
        /with\s+open\s*\(/g,
        /read\s*\(/g,
        /write\s*\(/g,
      ];
      
      const hasFileOps = fileOperations.some(pattern => pattern.test(codeWithoutStrings));
      if (hasFileOps && !code.includes("try:") && !code.includes("except FileNotFoundError")) {
        issues.push({
          type: "python-filenotfounderror",
          severity: "medium",
          description: "File operations detected without FileNotFoundError handling. Consider wrapping file operations in try/except FileNotFoundError.",
        });
      }

      // 5. TypeError: Operations on potentially None values
      // Check for method calls or operations on variables that could be None
      const methodCallPattern = /([a-zA-Z_][a-zA-Z0-9_]*)\\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g;
      const methodCalls = [...codeWithoutStrings.matchAll(methodCallPattern)];
      const checkedMethods = new Set<string>();
      
      methodCalls.forEach((match) => {
        const objName = match[1];
        
        // Skip safe patterns
        if (['self', 'cls', 'super'].includes(objName)) {
          return;
        }
        
        // Check if obj is assigned from function that could return None
        const couldBeNone = 
          code.includes(`${objName} = None`) ||
          code.includes(`= ${objName}()`) ||
          code.includes(`return ${objName}`);
        
        // Skip if already checked or clearly not None
        if (checkedMethods.has(objName) || !couldBeNone) {
          return;
        }
        
        // Check if there's a None check before this method call
        const hasNoneCheck = 
          code.includes(`if ${objName} is not None`) ||
          code.includes(`if ${objName} != None`) ||
          code.includes(`assert ${objName} is not None`) ||
          code.includes(`if ${objName}:`);
        
        if (!hasNoneCheck) {
          checkedMethods.add(objName);
          issues.push({
            type: "python-typeerror",
            severity: "high",
            description: `Method call on "${objName}" may raise TypeError if ${objName} is None. Consider adding a None check before calling methods.`,
            variable: objName,
            code: match[0],
          });
        }
      });

      // 6. ValueError: Type conversions without validation
      // Pattern: int(), float() on potentially invalid input
      const conversionPatterns = [
        /int\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\)/g,
        /float\s*\(([a-zA-Z_][a-zA-Z0-9_]*)\)/g,
      ];
      
      conversionPatterns.forEach((pattern) => {
        const conversions = [...codeWithoutStrings.matchAll(pattern)];
        conversions.forEach((match) => {
          const varName = match[1];
          
          // Check if there's validation
          const hasValidation = 
            code.includes(`try:`) ||
            code.includes(`isinstance(${varName}`) ||
            code.includes(`type(${varName})`) ||
            code.includes(`str(${varName}).isdigit()`) ||
            code.includes(`if ${varName}.isdigit()`);
          
          // Check if it's user input
          const isUserInput = 
            code.includes(`request.`) ||
            code.includes(`req.`) ||
            code.includes(`form[`) ||
            code.includes(`args[`) ||
            code.includes(`query[`);
          
          if (!hasValidation && isUserInput) {
            issues.push({
              type: "python-valueerror",
              severity: "medium",
              description: `Type conversion on "${varName}" may raise ValueError if input is invalid. Consider validating input or using try/except ValueError.`,
              variable: varName,
              code: match[0],
            });
          }
        });
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
  description: "Generates fetch commands to test discovered issues in the API. Only generates tests for issues that were actually detected by the code analyzer. Returns empty test cases array if no valid issues are provided.",
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

    // Only generate tests if we have valid issues
    if (!issues || !Array.isArray(issues) || issues.length === 0) {
      return {
        testCasesGenerated: 0,
        testCases: [],
      };
    }

    issues.forEach((issue: any, index: number) => {
      // Ensure issue has required fields
      if (!issue || !issue.type) {
        return;
      }

      switch (issue.type) {
        case "divide-by-zero":
          // Only generate tests if variable is specified and valid
          if (!issue.variable || typeof issue.variable !== "string") {
            return; // Skip invalid divide-by-zero issues
          }

          // Generate test cases for divide by zero
          testCases.push({
            id: `test-${index + 1}`,
            name: `Divide by Zero Test - ${issue.variable}`,
            issue: issue.type,
            severity: issue.severity || "high",
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
            severity: issue.severity || "high",
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

        case "unhandled-exceptions":
          // Test scenarios that might trigger unhandled exceptions
          testCases.push({
            id: `test-${index + 1}`,
            name: "Unhandled Exception Test - Invalid Input",
            issue: issue.type,
            severity: issue.severity || "high",
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { invalid: "data" },
              expectedBehavior: "Should catch and handle exceptions gracefully instead of crashing",
            },
            curlCommand: `curl "${baseUrl}${route}?invalid=data"`,
          });
          testCases.push({
            id: `test-${index + 1}b`,
            name: "Unhandled Exception Test - Missing Required Fields",
            issue: issue.type,
            severity: issue.severity || "high",
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: {},
              expectedBehavior: "Should handle missing required parameters without unhandled exceptions",
            },
            curlCommand: `curl "${baseUrl}${route}"`,
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

        case "python-keyerror":
          // Test with missing dictionary key
          if (issue.variable) {
            testCases.push({
              id: `test-${index + 1}`,
              name: `KeyError Test - Missing Key in ${issue.variable}`,
              issue: issue.type,
              severity: issue.severity || "medium",
              fetchCommand: {
                url: `${baseUrl}${route}`,
                method: "GET",
                params: { [issue.variable]: "nonexistent_key" },
                expectedBehavior: "Should handle missing dictionary keys gracefully (use .get() or check with 'in')",
              },
              curlCommand: `curl "${baseUrl}${route}?${issue.variable}=nonexistent_key"`,
            });
          }
          break;

        case "python-indexerror":
          // Test with out-of-range list index
          if (issue.variable) {
            testCases.push({
              id: `test-${index + 1}`,
              name: `IndexError Test - Out of Range for ${issue.variable}`,
              issue: issue.type,
              severity: issue.severity || "medium",
              fetchCommand: {
                url: `${baseUrl}${route}`,
                method: "GET",
                params: { index: "99999" },
                expectedBehavior: "Should handle out-of-range list indices gracefully",
              },
              curlCommand: `curl "${baseUrl}${route}?index=99999"`,
            });
          }
          break;

        case "python-attributeerror":
          // Test with None object
          if (issue.variable) {
            testCases.push({
              id: `test-${index + 1}`,
              name: `AttributeError Test - None Object ${issue.variable}`,
              issue: issue.type,
              severity: issue.severity || "medium",
              fetchCommand: {
                url: `${baseUrl}${route}`,
                method: "GET",
                params: { [issue.variable]: "null" },
                expectedBehavior: "Should handle None objects gracefully before accessing attributes",
              },
              curlCommand: `curl "${baseUrl}${route}?${issue.variable}=null"`,
            });
          }
          break;

        case "python-typeerror":
          // Test with None value
          if (issue.variable) {
            testCases.push({
              id: `test-${index + 1}`,
              name: `TypeError Test - None Value for ${issue.variable}`,
              issue: issue.type,
              severity: issue.severity || "high",
              fetchCommand: {
                url: `${baseUrl}${route}`,
                method: "GET",
                params: { [issue.variable]: "null" },
                expectedBehavior: "Should check for None before calling methods to avoid TypeError",
              },
              curlCommand: `curl "${baseUrl}${route}?${issue.variable}=null"`,
            });
          }
          break;

        case "python-valueerror":
          // Test with invalid type conversion input
          if (issue.variable) {
            testCases.push({
              id: `test-${index + 1}`,
              name: `ValueError Test - Invalid Input for ${issue.variable}`,
              issue: issue.type,
              severity: issue.severity || "medium",
              fetchCommand: {
                url: `${baseUrl}${route}`,
                method: "GET",
                params: { [issue.variable]: "not-a-number" },
                expectedBehavior: "Should validate input before type conversion or catch ValueError",
              },
              curlCommand: `curl "${baseUrl}${route}?${issue.variable}=not-a-number"`,
            });
          }
          break;

        case "python-filenotfounderror":
          // Test with file operations
          testCases.push({
            id: `test-${index + 1}`,
            name: "FileNotFoundError Test",
            issue: issue.type,
            severity: issue.severity || "medium",
            fetchCommand: {
              url: `${baseUrl}${route}`,
              method: "GET",
              params: { file: "nonexistent_file.txt" },
              expectedBehavior: "Should handle missing files gracefully with try/except FileNotFoundError",
            },
            curlCommand: `curl "${baseUrl}${route}?file=nonexistent_file.txt"`,
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
        } else if (testCase.issue === "unhandled-exceptions") {
          // Check for unhandled exceptions (500 errors or exception traces)
          const responseText = typeof responseBody === "string" ? responseBody : JSON.stringify(responseBody);
          const hasExceptionTrace = 
            responseText.includes("Traceback") ||
            responseText.includes("Exception:") ||
            responseText.includes("Error:") ||
            responseText.includes("at ") ||
            responseText.includes("stack trace");
          
          if (response.status === 500 && hasExceptionTrace) {
            testResult.passed = false;
            testResult.analysis = "🔴 ISSUE CONFIRMED: Unhandled exception detected - API returns 500 with exception trace";
          } else if (response.status === 500) {
            testResult.passed = false;
            testResult.analysis = "🔴 ISSUE CONFIRMED: Unhandled exception detected - API returns 500 error";
          } else if (response.status >= 400 && response.status < 500) {
            testResult.passed = true;
            testResult.analysis = "✅ PASS: API handles exceptions gracefully (returns proper error response)";
          } else {
            testResult.passed = true;
            testResult.analysis = "✅ PASS: No unhandled exceptions detected";
          }
        } else if (testCase.issue === "missing-error-handling") {
          testResult.passed = response.status < 500;
          testResult.analysis =
            response.status < 500
              ? "✅ PASS: No server error detected"
              : "🔴 ISSUE CONFIRMED: Server error occurred (may indicate missing error handling)";
        } else if (testCase.issue.startsWith("python-")) {
          // Python-specific error detection
          const responseText = typeof responseBody === "string" ? responseBody : JSON.stringify(responseBody);
          const errorType = testCase.issue.replace("python-", "");
          
          const hasErrorTrace = 
            responseText.includes("KeyError") ||
            responseText.includes("IndexError") ||
            responseText.includes("AttributeError") ||
            responseText.includes("TypeError") ||
            responseText.includes("ValueError") ||
            responseText.includes("FileNotFoundError") ||
            responseText.includes("Traceback") ||
            responseText.includes(errorType);
          
          if (response.status === 500 && hasErrorTrace) {
            testResult.passed = false;
            testResult.analysis = `🔴 ISSUE CONFIRMED: ${errorType} detected - API returns 500 with error trace`;
          } else if (response.status === 500) {
            testResult.passed = false;
            testResult.analysis = `🔴 ISSUE CONFIRMED: ${errorType} may have occurred - API returns 500 error`;
          } else if (response.status >= 400 && response.status < 500) {
            testResult.passed = true;
            testResult.analysis = `✅ PASS: API handles ${errorType} gracefully (returns proper error response)`;
          } else {
            testResult.passed = true;
            testResult.analysis = `✅ PASS: No ${errorType} detected`;
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
