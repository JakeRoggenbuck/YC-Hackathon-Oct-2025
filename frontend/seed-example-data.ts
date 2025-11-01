#!/usr/bin/env node

/**
 * Script to seed example agent result data into Convex
 * Run with: npx tsx seed-example-data.ts
 */

import { ConvexHttpClient } from "convex/browser";
import dotenv from "dotenv";

dotenv.config({ path: "../.env" });

const CONVEX_URL = process.env.CONVEX_URL;
if (!CONVEX_URL) {
  console.error("CONVEX_URL not found in environment");
  process.exit(1);
}

const client = new ConvexHttpClient(CONVEX_URL);

const exampleSummary = `# API Testing Report

## Executive Summary
Analyzed API at https://api.example.com against repository https://github.com/user/repo
Total Issues Found: 5 (3 Critical, 2 High)

## Critical Issues

### 1. Divide by Zero Error - /api/calculate
**Severity:** CRITICAL
**Location:** src/routes/calculator.py:45
**Description:** Unvalidated division operation allows divide-by-zero errors
**Test Result:** Confirmed - Returns 500 Internal Server Error
**Recommendation:** Add validation for b == 0

### 2. Unhandled Exception - /api/users/{id}
**Severity:** CRITICAL  
**Location:** src/routes/users.py:23
**Description:** KeyError not caught when user_id doesn't exist
**Test Result:** Confirmed - Returns 500 instead of 404
**Recommendation:** Use .get() method or try-except block

### 3. SQL Injection Vulnerability - /api/search
**Severity:** CRITICAL
**Location:** src/routes/search.py:12
**Description:** User input directly concatenated into SQL query
**Test Result:** Confirmed - Vulnerable to SQL injection
**Recommendation:** Use parameterized queries

## High Priority Issues

### 4. Missing Input Validation - /api/posts
**Severity:** HIGH
**Location:** src/routes/posts.py:34
**Description:** No validation on POST data fields
**Test Result:** Confirmed - Accepts arbitrary data
**Recommendation:** Use Pydantic models for validation

### 5. Null Pointer Exception - /api/profile
**Severity:** HIGH
**Location:** src/routes/profile.py:18
**Description:** Accessing attributes without null check
**Test Result:** Confirmed - Returns 500 for users without profiles
**Recommendation:** Add null checks before attribute access

## Summary
- Total Endpoints Tested: 12
- Endpoints with Issues: 5
- Endpoints Passed: 7`;

async function seedData() {
  console.log("Creating example agent request...");
  
  const requestId = await client.mutation("agentRequests:insertRequest", {
    email: "demo@example.com",
    githubUrl: "https://github.com/user/demo-repo",
    hostedApiUrl: "https://api.example.com",
  });

  console.log("Request created:", requestId);

  await client.mutation("agentRequests:setAgentToStarted", { requestId });
  console.log("Request marked as started");

  console.log("Storing example result...");
  
  const resultId = await client.mutation("agentResults:insertResult", {
    requestId,
    email: "demo@example.com",
    githubUrl: "https://github.com/user/demo-repo",
    hostedApiUrl: "https://api.example.com",
    resultSummary: exampleSummary,
  });

  console.log("Result stored:", resultId);
  console.log("\nExample data seeded successfully!");
  console.log("You can now query results with:");
  console.log(`  curl http://localhost:8000/get-results/demo@example.com`);
}

seedData().catch(console.error);
