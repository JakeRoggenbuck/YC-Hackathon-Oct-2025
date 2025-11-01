import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const seedExampleResults = mutation({
  args: {},
  handler: async (ctx) => {
    const exampleSummary = `# API Testing Report

## Executive Summary
Analyzed API at https://api.example.com against repository https://github.com/user/repo
Total Issues Found: 5 (3 Critical, 2 High)

## Critical Issues

### 1. Divide by Zero Error - /api/calculate
**Severity:** CRITICAL
**Location:** src/routes/calculator.py:45
**Description:** Unvalidated division operation allows divide-by-zero errors
**Code:**
\`\`\`python
def calculate(a: int, b: int):
    return a / b  # No validation for b == 0
\`\`\`
**Test Result:** Confirmed - Returns 500 Internal Server Error
**Reproduction:**
\`\`\`bash
curl -X POST https://api.example.com/api/calculate -d '{"a": 10, "b": 0}'
\`\`\`
**Recommendation:** Add validation: \`if b == 0: raise ValueError("Division by zero")\`

### 2. Unhandled Exception - /api/users/{id}
**Severity:** CRITICAL
**Location:** src/routes/users.py:23
**Description:** KeyError not caught when user_id doesn't exist in database
**Code:**
\`\`\`python
def get_user(user_id: str):
    return users[user_id]  # Raises KeyError if not found
\`\`\`
**Test Result:** Confirmed - Returns 500 instead of 404
**Reproduction:**
\`\`\`bash
curl https://api.example.com/api/users/nonexistent
\`\`\`
**Recommendation:** Use \`.get()\` method or wrap in try-except block

### 3. SQL Injection Vulnerability - /api/search
**Severity:** CRITICAL
**Location:** src/routes/search.py:12
**Description:** User input directly concatenated into SQL query
**Code:**
\`\`\`python
def search(query: str):
    sql = f"SELECT * FROM items WHERE name LIKE '%{query}%'"
    return db.execute(sql)
\`\`\`
**Test Result:** Confirmed - Vulnerable to SQL injection
**Reproduction:**
\`\`\`bash
curl "https://api.example.com/api/search?q='; DROP TABLE items;--"
\`\`\`
**Recommendation:** Use parameterized queries

## High Priority Issues

### 4. Missing Input Validation - /api/posts
**Severity:** HIGH
**Location:** src/routes/posts.py:34
**Description:** No validation on POST data fields
**Code:**
\`\`\`python
@app.post("/posts")
def create_post(data: dict):
    return db.insert(data)  # No validation
\`\`\`
**Test Result:** Confirmed - Accepts arbitrary data
**Recommendation:** Use Pydantic models for validation

### 5. Null Pointer Exception - /api/profile
**Severity:** HIGH  
**Location:** src/routes/profile.py:18
**Description:** Accessing attributes without null check
**Code:**
\`\`\`python
def get_profile(user_id: str):
    user = get_user(user_id)
    return user.profile.bio  # No check if profile exists
\`\`\`
**Test Result:** Confirmed - Returns 500 for users without profiles
**Recommendation:** Add null checks before attribute access

## Summary Statistics
- Total Endpoints Tested: 12
- Endpoints with Issues: 5
- Endpoints Passed: 7
- Test Coverage: 100%

## Recommendations Priority
1. Fix all CRITICAL issues immediately
2. Implement comprehensive input validation
3. Add proper error handling and logging
4. Use parameterized queries for all database operations
5. Add unit tests for edge cases`;

    const resultId = await ctx.db.insert("agentResults", {
      requestId: "mock_request_id" as any,
      email: "test@example.com",
      githubUrl: "https://github.com/user/repo",
      hostedApiUrl: "https://api.example.com",
      resultSummary: exampleSummary,
      completedAt: Date.now(),
    });

    return { success: true, resultId, message: "Example result seeded" };
  },
});
