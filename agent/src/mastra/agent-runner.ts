import { apiTestingAgent } from "./agents/test-agent";
import { startQueueMonitoring } from "./tools/convex-connection";
import { ConvexHttpClient } from "convex/browser";
import dotenv from "dotenv";

dotenv.config();

const getConvexClient = () => {
  const convexUrl = process.env.CONVEX_URL;
  if (!convexUrl) {
    throw new Error("CONVEX_URL environment variable is not set");
  }
  return new ConvexHttpClient(convexUrl);
};

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

Request ID: ${request._id}
Email: ${request.email}

Please:
1. Explore the repository structure to find API route files
2. Analyze the code for potential issues (divide-by-zero, unhandled exceptions, validation issues, etc.)
3. Generate test cases for each discovered issue
4. Execute the tests against the hosted API
5. Report the findings
6. When complete, use the insert-agent-result tool to store your results in Convex with:
   - requestId: ${request._id}
   - email: ${request.email}
   - githubUrl: ${request.githubUrl}
   - hostedApiUrl: ${request.hostedApiUrl}
   - resultSummary: your comprehensive analysis summary

The results will be sent to: ${request.email}
`;

      console.log("\nSending prompt to agent...");
      
      const response = await apiTestingAgent.generate(prompt);

      console.log("\nAgent completed analysis");
      console.log("Response:", response.text);

      // Write results to Convex agentResults table
      try {
        const client = getConvexClient();
        const resultId = await client.mutation("agentResults:insertResult" as any, {
          requestId: request._id,
          email: request.email,
          githubUrl: request.githubUrl,
          hostedApiUrl: request.hostedApiUrl,
          resultSummary: response.text,
        });
        
        console.log(`\nResults written to Convex agentResults with ID: ${resultId}`);
      } catch (error) {
        console.error("\nError writing to Convex agentResults:", error);
      }

      // Also send to backend for email notification (if needed)
      try {
        await fetch("http://localhost:8000/store-result", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: request._id,
            email: request.email,
            github_url: request.githubUrl,
            hosted_api_url: request.hostedApiUrl,
            result_summary: response.text,
          }),
        });
        console.log(`\nResults also sent to backend for email to: ${request.email}`);
      } catch (error) {
        console.error("\nError sending results to backend:", error);
      }
      
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
