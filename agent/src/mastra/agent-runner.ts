import { apiTestingAgent } from "./agents/test-agent";
import { startQueueMonitoring } from "./tools/convex-connection";
import dotenv from "dotenv";

dotenv.config();

console.log("Starting API Testing Agent Queue Monitor");
console.log(`Convex URL: ${process.env.CONVEX_URL}`);

const stopMonitoring = startQueueMonitoring(
  async (request) => {
    console.log("\nNew request received:", request);

    try {
      const repoMatch = request.githubUrl.match(/github\.com\/([^/]+)\/([^/]+)/);
      if (!repoMatch) {
        console.error("Invalid GitHub URL format:", request.githubUrl);
        return;
      }

      const [, repoOwner, repoName] = repoMatch;

      const prompt = `
Analyze and test the API at ${request.hostedApiUrl}

Repository: ${request.githubUrl}
Owner: ${repoOwner}
Repo: ${repoName}

Please:
1. Explore the repository structure to find API route files
2. Analyze the code for potential issues (divide-by-zero, unhandled exceptions, validation issues, etc.)
3. Generate test cases for each discovered issue
4. Execute the tests against the hosted API
5. Report the findings

The results will be sent to: ${request.email}
`;

      console.log("\nSending prompt to agent...");
      
      const response = await apiTestingAgent.generate(prompt);

      console.log("\nAgent completed analysis");
      console.log("Response:", response.text);

      // TODO: Send email with results
      console.log(`\nWould send results to: ${request.email}`);
      
    } catch (error) {
      console.error("\nError processing request:", error);
    }
  },
  5000
);

process.on("SIGINT", () => {
  console.log("\n\nShutting down agent queue monitor...");
  stopMonitoring();
  process.exit(0);
});

console.log("\nAgent queue monitor running. Press Ctrl+C to stop.\n");
