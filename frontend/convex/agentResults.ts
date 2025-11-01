import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const insertResult = mutation({
  args: {
    requestId: v.id("agentRequests"),
    email: v.string(),
    githubUrl: v.string(),
    hostedApiUrl: v.string(),
    resultSummary: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("agentResults", {
      requestId: args.requestId,
      email: args.email,
      githubUrl: args.githubUrl,
      hostedApiUrl: args.hostedApiUrl,
      resultSummary: args.resultSummary,
      completedAt: Date.now(),
    });
  },
});

export const getResultByRequestId = query({
  args: {
    requestId: v.id("agentRequests"),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agentResults")
      .withIndex("by_request_id", (q) => q.eq("requestId", args.requestId))
      .first();
  },
});

export const getResultsByEmail = query({
  args: {
    email: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agentResults")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .order("desc")
      .collect();
  },
});

export const getAllResults = query({
  handler: async (ctx) => {
    return await ctx.db
      .query("agentResults")
      .withIndex("by_completed_at")
      .order("desc")
      .collect();
  },
});
