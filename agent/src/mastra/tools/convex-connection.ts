import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { ConvexHttpClient } from "convex/browser";

const getConvexClient = () => {
  const convexUrl = process.env.CONVEX_URL;
  if (!convexUrl) {
    throw new Error("CONVEX_URL environment variable is not set");
  }
  return new ConvexHttpClient(convexUrl);
};

export const fetchUnstartedRequestsTool = createTool({
  id: "fetch-unstarted-requests",
  description: "Fetches all unstarted agent requests from the Convex queue.",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    requests: z.array(
      z.object({
        _id: z.string(),
        _creationTime: z.number(),
        email: z.string(),
        githubUrl: z.string(),
        hostedApiUrl: z.string(),
        isAgentStarted: z.boolean(),
        createdAt: z.number(),
      })
    ),
    count: z.number(),
    error: z.string().optional(),
  }),
  execute: async () => {
    try {
      const client = getConvexClient();
      const requests = await client.query("agentRequests:getUnstarted");

      return {
        success: true,
        requests: requests || [],
        count: requests?.length || 0,
      };
    } catch (error: any) {
      console.error("Error fetching unstarted requests:", error);
      return {
        success: false,
        requests: [],
        count: 0,
        error: error.message || "Failed to fetch requests",
      };
    }
  },
});

export const markRequestAsStartedTool = createTool({
  id: "mark-request-started",
  description: "Marks an agent request as started in Convex.",
  inputSchema: z.object({
    requestId: z.string().describe("The Convex document ID of the request"),
  }),
  outputSchema: z.object({
    success: z.boolean(),
    requestId: z.string(),
    error: z.string().optional(),
  }),
  execute: async ({ requestId }) => {
    try {
      const client = getConvexClient();
      await client.mutation("agentRequests:setAgentToStarted", {
        requestId,
      });

      return {
        success: true,
        requestId,
      };
    } catch (error: any) {
      console.error("Error marking request as started:", error);
      return {
        success: false,
        requestId,
        error: error.message || "Failed to mark request as started",
      };
    }
  },
});

export const processNextRequestTool = createTool({
  id: "process-next-request",
  description: "Fetches the next unstarted request and marks it as started.",
  inputSchema: z.object({}),
  outputSchema: z.object({
    success: z.boolean(),
    request: z
      .object({
        _id: z.string(),
        email: z.string(),
        githubUrl: z.string(),
        hostedApiUrl: z.string(),
        createdAt: z.number(),
      })
      .optional(),
    message: z.string(),
    error: z.string().optional(),
  }),
  execute: async () => {
    try {
      const client = getConvexClient();
      const requests = await client.query("agentRequests:getUnstarted");

      if (!requests || requests.length === 0) {
        return {
          success: true,
          message: "No unstarted requests found in queue",
        };
      }

      const nextRequest = requests[0];

      await client.mutation("agentRequests:setAgentToStarted", {
        requestId: nextRequest._id,
      });

      console.log(`Processing request ${nextRequest._id}:`, {
        email: nextRequest.email,
        githubUrl: nextRequest.githubUrl,
        hostedApiUrl: nextRequest.hostedApiUrl,
      });

      return {
        success: true,
        request: {
          _id: nextRequest._id,
          email: nextRequest.email,
          githubUrl: nextRequest.githubUrl,
          hostedApiUrl: nextRequest.hostedApiUrl,
          createdAt: nextRequest.createdAt,
        },
        message: "Request fetched and marked as started",
      };
    } catch (error: any) {
      console.error("Error processing next request:", error);
      return {
        success: false,
        message: "Failed to process next request",
        error: error.message || "Unknown error",
      };
    }
  },
});

export const insertAgentResultTool = createTool({
  id: "insert-agent-result",
  description: "Writes the agent's analysis results to the Convex agentResults table. Use this when you have completed your analysis and want to store the results.",
  inputSchema: z.object({
    requestId: z.string().describe("The Convex document ID of the original agent request"),
    email: z.string().describe("The email address associated with the request"),
    githubUrl: z.string().describe("The GitHub repository URL that was analyzed"),
    hostedApiUrl: z.string().describe("The hosted API URL that was tested"),
    resultSummary: z.string().describe("A comprehensive summary of the analysis results, including issues found, test results, and recommendations"),
  }),
  outputSchema: z.union([
    z.object({
      success: z.boolean(),
      resultId: z.string().optional(),
      error: z.string().optional(),
    }),
    z.string(), // Allow string return in case of JSON conversion errors
  ]),
  execute: async (args) => {
    try {
      // Log what we receive to debug - catch JSON conversion errors
      try {
        console.log("insert-agent-result tool called with args:", JSON.stringify(args, null, 2));
      } catch (jsonError: any) {
        console.log("insert-agent-result tool called with args (could not stringify):", String(args));
      }
      
      if (!args || typeof args !== 'object') {
        return `Invalid args: ${typeof args}. Expected object.`;
      }

      // Extract arguments from context if they're nested, otherwise use args directly
      const actualArgs = (args as any).context || args;
      const { requestId, email, githubUrl, hostedApiUrl, resultSummary } = actualArgs;
      
      // Validate all required parameters are present
      const missing = [];
      if (!requestId) missing.push('requestId');
      if (!email) missing.push('email');
      if (!githubUrl) missing.push('githubUrl');
      if (!hostedApiUrl) missing.push('hostedApiUrl');
      if (!resultSummary) missing.push('resultSummary');
      
      if (missing.length > 0) {
        console.error("Missing required parameters:", missing);
        try {
          console.error("Received args keys:", Object.keys(args));
          console.error("Extracted actualArgs keys:", actualArgs ? Object.keys(actualArgs) : 'actualArgs is null/undefined');
          console.error("Args values:", { 
            requestId: !!requestId, 
            email: !!email, 
            githubUrl: !!githubUrl, 
            hostedApiUrl: !!hostedApiUrl, 
            resultSummary: !!resultSummary 
          });
        } catch (jsonError) {
          console.error("Could not log args due to JSON conversion error");
        }
        const receivedKeys = actualArgs ? Object.keys(actualArgs).join(', ') : 'none';
        return `Missing required parameters: ${missing.join(', ')}. Extracted keys from args: ${receivedKeys}`;
      }

      try {
        console.log("Calling Convex mutation with parameters:", {
          requestId,
          email,
          githubUrl,
          hostedApiUrl,
          resultSummaryLength: resultSummary?.length || 0,
        });
      } catch (jsonError) {
        console.log("Calling Convex mutation (could not log parameters due to JSON conversion error)");
      }

      const client = getConvexClient();
      const mutationArgs = {
        requestId: String(requestId),
        email: String(email),
        githubUrl: String(githubUrl),
        hostedApiUrl: String(hostedApiUrl),
        resultSummary: String(resultSummary),
      };
      
      try {
        console.log("Mutation args being sent:", mutationArgs);
      } catch (jsonError) {
        console.log("Mutation args being sent (could not log due to JSON conversion error)");
      }
      
      const resultId = await client.mutation("agentResults:insertResult" as any, mutationArgs);

      console.log(`Agent result written to Convex with ID: ${String(resultId)}`);
      
      try {
        return {
          success: true,
          resultId: String(resultId),
        };
      } catch (jsonError: any) {
        // If we can't return structured JSON, return a string
        return `Success: Agent result written to Convex with ID: ${String(resultId)}`;
      }
    } catch (error: any) {
      console.error("Error inserting agent result:", error);
      if (error.stack) {
        console.error("Error stack:", error.stack);
      }
      // Return error as string instead of structured JSON
      const errorMessage = error.message || String(error) || "Failed to insert agent result";
      return `Error: ${errorMessage}`;
    }
  },
});

export const startQueueMonitoring = (
  onNewRequest: (request: {
    _id: string;
    email: string;
    githubUrl: string;
    hostedApiUrl: string;
  }) => void,
  intervalMs: number = 5000
) => {
  const client = getConvexClient();
  
  console.log(`Starting queue monitoring (interval: ${intervalMs}ms)`);

  const checkQueue = async () => {
    try {
      const requests = await client.query("agentRequests:getUnstarted");
      
      if (requests && requests.length > 0) {
        const nextRequest = requests[0];
        
        await client.mutation("agentRequests:setAgentToStarted", {
          requestId: nextRequest._id,
        });

        onNewRequest({
          _id: nextRequest._id,
          email: nextRequest.email,
          githubUrl: nextRequest.githubUrl,
          hostedApiUrl: nextRequest.hostedApiUrl,
        });
      }
    } catch (error) {
      console.error("Queue monitoring error:", error);
    }
  };

  checkQueue();
  const intervalId = setInterval(checkQueue, intervalMs);

  return () => {
    clearInterval(intervalId);
    console.log("Queue monitoring stopped");
  };
};
