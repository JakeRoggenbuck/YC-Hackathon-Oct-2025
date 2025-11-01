import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

interface WorkflowData {
  email: string;
  apiUrl: string;
  githubUrl: string;
}

interface StartAgentResponse {
  status?: string;
  message?: string;
}

interface GetResultsResponse {
  status: string;
  results: Array<{
    _id: string;
    _creationTime: number;
    email: string;
    githubUrl: string;
    hostedApiUrl: string;
    resultSummary?: string;
  }>;
}

interface RunPipelineResponse {
  status: string;
  message: string;
  email: string;
  github_repo: string;
  issues_detected?: number;
  github_issues_created?: number;
  github_issues_failed?: number;
  email_sent?: boolean;
}

export type WorkflowStatus = 
  | "idle" 
  | "starting" 
  | "waiting-for-results" 
  | "running-pipeline" 
  | "complete" 
  | "error";

interface WorkflowState {
  status: WorkflowStatus;
  error: string | null;
  data: WorkflowData | null;
  pipelineResult: RunPipelineResponse | null;
}

const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_POLLING_ATTEMPTS = 100; // 5 minutes max (100 * 3s)

export function useAgentWorkflow() {
  const queryClient = useQueryClient();

  // Step 1: Start the agent
  const startAgentMutation = useMutation<StartAgentResponse, Error, WorkflowData>({
    mutationFn: async (data: WorkflowData) => {
      const payload = {
        email: data.email,
        github_repo: data.githubUrl,
        hosted_api_url: data.apiUrl,
      };
      
      const res = await apiRequest("POST", "http://localhost:8000/start-agent", payload);
      
      try {
        return await res.json();
      } catch {
        return { status: "success" };
      }
    },
  });

  // Step 2: Poll for results (only enabled when email is set)
  const useResultsPolling = (email: string | null, enabled: boolean) => {
    return useQuery<GetResultsResponse, Error>({
      queryKey: ["agent-results", email],
      queryFn: async () => {
        if (!email) throw new Error("Email is required");
        
        const res = await apiRequest("GET", `http://localhost:8000/get-results/${encodeURIComponent(email)}`);
        const data = await res.json();
        
        // Check if we have results with a resultSummary
        if (data.results && data.results.length > 0) {
          const latestResult = data.results[0];
          if (latestResult.resultSummary && latestResult.resultSummary.length > 0) {
            return data;
          }
        }
        
        // If no valid results yet, throw to continue polling
        throw new Error("Results not ready yet");
      },
      enabled: enabled && !!email,
      refetchInterval: (query) => {
        // Stop polling if we have data or if we've had too many errors
        if (query.state.data || query.state.error) {
          return false;
        }
        return POLLING_INTERVAL;
      },
      retry: MAX_POLLING_ATTEMPTS,
      retryDelay: POLLING_INTERVAL,
    });
  };

  // Step 3: Run the pipeline
  const runPipelineMutation = useMutation<RunPipelineResponse, Error, WorkflowData>({
    mutationFn: async (data: WorkflowData) => {
      const payload = {
        email: data.email,
        github_repo: data.githubUrl,
        create_github_issues: true,
      };
      
      const res = await apiRequest("POST", "http://localhost:8000/run-pipeline", payload);
      return await res.json();
    },
  });

  return {
    startAgentMutation,
    useResultsPolling,
    runPipelineMutation,
    queryClient,
  };
}
