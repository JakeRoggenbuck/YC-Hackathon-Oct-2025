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
});