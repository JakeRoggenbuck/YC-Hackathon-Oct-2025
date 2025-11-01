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
  outputSchema: z.object({
    success: z.boolean(),
    resultId: z.string().optional(),
    error: z.string().optional(),
  }),
  execute: async (args) => {
    try {
      // Log what we receive to debug
      console.log("insert-agent-result tool called with args:", JSON.stringify(args, null, 2));
      
      if (!args || typeof args !== 'object') {
        return {
          success: false,
          error: `Invalid args: ${typeof args}. Expected object.`,
        };
      }

      const { requestId, email, githubUrl, hostedApiUrl, resultSummary } = args;
      
      // Validate all required parameters are present
      const missing = [];
      if (!requestId) missing.push('requestId');
      if (!email) missing.push('email');
      if (!githubUrl) missing.push('githubUrl');
      if (!hostedApiUrl) missing.push('hostedApiUrl');
      if (!resultSummary) missing.push('resultSummary');
      
      if (missing.length > 0) {
        console.error("Missing required parameters:", missing);
        console.error("Received args keys:", Object.keys(args));
        console.error("Args values:", { 
          requestId: !!requestId, 
          email: !!email, 
          githubUrl: !!githubUrl, 
          hostedApiUrl: !!hostedApiUrl, 
          resultSummary: !!resultSummary 
        });
        return {
          success: false,
          error: `Missing required parameters: ${missing.join(', ')}. Received keys: ${Object.keys(args).join(', ')}`,
        };
      }

      console.log("Calling Convex mutation with parameters:", {
        requestId,
        email,
        githubUrl,
        hostedApiUrl,
        resultSummaryLength: resultSummary?.length || 0,
      });

      const client = getConvexClient();
      const mutationArgs = {
        requestId: String(requestId),
        email: String(email),
        githubUrl: String(githubUrl),
        hostedApiUrl: String(hostedApiUrl),
        resultSummary: String(resultSummary),
      };
      
      console.log("Mutation args being sent:", mutationArgs);
      
      const resultId = await client.mutation("agentResults:insertResult" as any, mutationArgs);

      console.log(`Agent result written to Convex with ID: ${resultId}`);
      
      return {
        success: true,
        resultId,
      };
    } catch (error: any) {
      console.error("Error inserting agent result:", error);
      console.error("Error stack:", error.stack);
      return {
        success: false,
        error: error.message || "Failed to insert agent result",
      };
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
