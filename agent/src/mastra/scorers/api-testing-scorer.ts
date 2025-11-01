import { createScorer } from "@mastra/core/scores";
import { z } from "zod";

export const issueDetectionAccuracyScorer = createScorer({
  name: "Issue Detection Accuracy",
  description: "Evaluates how accurately the agent detects real issues",
  type: "agent",
  judge: {
    model: "openai/gpt-4o-mini",
    instructions:
      "You are an expert evaluator of API testing accuracy. " +
      "Analyze the agent's output to extract metrics about detected and confirmed issues. " +
      "Return only the structured JSON matching the provided schema.",
  },
})
  .analyze({
    description: "Extract issue detection metrics from the output",
    outputSchema: z.object({
      detectedIssues: z.number(),
      confirmedIssues: z.number(),
    }),
    createPrompt: ({ run }) => {
      const output = (run.output?.[0]?.content as string) || "";
      return `Analyze the following agent output and extract:
1. The number of issues detected (detectedIssues)
2. The number of issues confirmed by testing (confirmedIssues)

Output:
"""
${output}
"""
Return JSON with detectedIssues and confirmedIssues fields.`;
    },
  })
  .generateScore(({ results }) => {
    const r = (results as any)?.analyzeStepResult || {};
    const detectedIssues = r.detectedIssues || 0;
    const confirmedIssues = r.confirmedIssues || 0;

    if (detectedIssues === 0) return 0;

    const accuracy = confirmedIssues / detectedIssues;
    return Math.max(0, Math.min(1, accuracy));
  })
  .generateReason(({ results, score }) => {
    const r = (results as any)?.analyzeStepResult || {};
    const detectedIssues = r.detectedIssues || 0;
    const confirmedIssues = r.confirmedIssues || 0;
    return `Detected ${detectedIssues} issues, confirmed ${confirmedIssues}. Accuracy: ${(score * 100).toFixed(1)}%`;
  });

export const testCoverageScorer = createScorer({
  name: "Test Coverage",
  description: "Evaluates test case coverage of detected issues",
  type: "agent",
  judge: {
    model: "openai/gpt-4o-mini",
    instructions:
      "You are an expert evaluator of test coverage. " +
      "Analyze the agent's output to extract metrics about issues found and test cases generated. " +
      "Return only the structured JSON matching the provided schema.",
  },
})
  .analyze({
    description: "Extract test coverage metrics from the output",
    outputSchema: z.object({
      issuesFound: z.number(),
      testCasesGenerated: z.number(),
    }),
    createPrompt: ({ run }) => {
      const output = (run.output?.[0]?.content as string) || "";
      return `Analyze the following agent output and extract:
1. The number of issues found (issuesFound)
2. The number of test cases generated (testCasesGenerated)

Output:
"""
${output}
"""
Return JSON with issuesFound and testCasesGenerated fields.`;
    },
  })
  .generateScore(({ results }) => {
    const r = (results as any)?.analyzeStepResult || {};
    const issuesFound = r.issuesFound || 0;
    const testCasesGenerated = r.testCasesGenerated || 0;

    if (issuesFound === 0) return 1;

    // Expect 2 tests per issue on average
    const coverage = Math.min(testCasesGenerated / (issuesFound * 2), 1);
    return Math.max(0, Math.min(1, coverage));
  })
  .generateReason(({ results, score }) => {
    const r = (results as any)?.analyzeStepResult || {};
    const issuesFound = r.issuesFound || 0;
    const testCasesGenerated = r.testCasesGenerated || 0;
    return `Generated ${testCasesGenerated} test cases for ${issuesFound} issues. Coverage: ${(score * 100).toFixed(1)}%`;
  });

export const scorers = {
  issueDetectionAccuracyScorer,
  testCoverageScorer,
};
