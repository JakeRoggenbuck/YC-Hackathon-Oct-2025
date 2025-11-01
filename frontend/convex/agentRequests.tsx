import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// InsertRequest (POST)
export const insertRequest = mutation({
  args: {
    email: v.string(),
    githubUrl: v.string(),
    hostedApiUrl: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("agentRequests", {
      email: args.email,
      githubUrl: args.githubUrl,
      hostedApiUrl: args.hostedApiUrl,
      isAgentStarted: false,
      createdAt: Date.now(),
    });
  },
});

// GetUnstarted (GET)
export const getUnstarted = query({
  handler: async (ctx) => {
    return await ctx.db
      .query("agentRequests")
      .withIndex("by_started_status", (q) => q.eq("isAgentStarted", false))
      .collect();
  },
});

// SetAgentToStarted (PUT)
export const setAgentToStarted = mutation({
  args: {
    requestId: v.id("agentRequests"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.requestId, {
      isAgentStarted: true,
    });
  },
});