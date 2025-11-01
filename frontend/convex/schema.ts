import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  agentRequests: defineTable({
    email: v.string(),
    githubUrl: v.string(),
    hostedApiUrl: v.string(),
    isAgentStarted: v.boolean(),
    createdAt: v.number(),
  })
    .index("by_started_status", ["isAgentStarted"])
    .index("by_created_at", ["createdAt"]),
  
  agentResults: defineTable({
    requestId: v.id("agentRequests"),
    email: v.string(),
    githubUrl: v.string(),
    hostedApiUrl: v.string(),
    resultSummary: v.string(),
    completedAt: v.number(),
  })
    .index("by_request_id", ["requestId"])
    .index("by_email", ["email"])
    .index("by_completed_at", ["completedAt"]),
});