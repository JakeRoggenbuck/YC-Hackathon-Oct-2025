import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useAgentWorkflow } from "@/hooks/use-agent-workflow";

const formSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  apiUrl: z.string().url("Please enter a valid API URL").refine(
    (url) => {
      try {
        const parsed = new URL(url);
        return parsed.protocol === "http:" || parsed.protocol === "https:";
      } catch {
        return false;
      }
    },
    { message: "API URL must use HTTP or HTTPS protocol" }
  ),
  githubUrl: z.string().min(1, "GitHub URL is required").url("Please enter a valid GitHub URL").refine(
    (url) => {
      try {
        const parsed = new URL(url);
        return parsed.hostname === "github.com" || parsed.hostname === "www.github.com";
      } catch {
        return false;
      }
    },
    { message: "Please enter a valid GitHub URL" }
  ),
});

type FormData = z.infer<typeof formSchema>;

interface TestingFormProps {
  onSuccess?: (data: FormData) => void;
  onWorkflowStatusChange?: (status: string, message?: string) => void;
}

export default function TestingForm({ onSuccess, onWorkflowStatusChange }: TestingFormProps) {
  const [isValidating, setIsValidating] = useState<{
    apiUrl?: boolean;
    githubUrl?: boolean;
  }>({});
  
  const [workflowEmail, setWorkflowEmail] = useState<string | null>(null);
  const [shouldPoll, setShouldPoll] = useState(false);
  const [workflowData, setWorkflowData] = useState<FormData | null>(null);

  const { startAgentMutation, useResultsPolling, runPipelineMutation } = useAgentWorkflow();
  
  // Poll for results when shouldPoll is true
  const resultsQuery = useResultsPolling(workflowEmail, shouldPoll);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, touchedFields },
    watch,
    trigger,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      email: "",
      apiUrl: "",
      githubUrl: "",
    },
  });

  // Handle workflow progression
  useEffect(() => {
    if (resultsQuery.data && workflowData && !runPipelineMutation.isSuccess) {
      // Results are ready, now run the pipeline
      onWorkflowStatusChange?.("running-pipeline", "Running AI analysis and creating issues...");
      runPipelineMutation.mutate(workflowData);
    }
  }, [resultsQuery.data, workflowData, runPipelineMutation.isSuccess]);

  useEffect(() => {
    if (runPipelineMutation.isSuccess && workflowData) {
      // Pipeline complete!
      onWorkflowStatusChange?.("complete", "Analysis complete! Check your email for results.");
      if (onSuccess) {
        onSuccess(workflowData);
      }
    }
  }, [runPipelineMutation.isSuccess, workflowData]);

  useEffect(() => {
    if (startAgentMutation.isSuccess && workflowEmail) {
      onWorkflowStatusChange?.("waiting-for-results", "Agent started. Waiting for test results...");
    }
  }, [startAgentMutation.isSuccess, workflowEmail]);

  useEffect(() => {
    if (resultsQuery.isError) {
      const errorCount = resultsQuery.failureCount || 0;
      if (errorCount < 100) {
        onWorkflowStatusChange?.("waiting-for-results", `Still processing... (${Math.floor(errorCount * 3 / 60)}m ${(errorCount * 3) % 60}s)`);
      }
    }
  }, [resultsQuery.isError, resultsQuery.failureCount]);

  const apiUrlValue = watch("apiUrl");
  const githubUrlValue = watch("githubUrl");

  const handleFieldBlur = async (field: "apiUrl" | "githubUrl") => {
    setIsValidating({ ...isValidating, [field]: true });
    await trigger(field);
    setTimeout(() => {
      setIsValidating({ ...isValidating, [field]: false });
    }, 300);
  };

  const onSubmit = async (data: FormData) => {
    console.log("Form submitted:", data);
    try {
      setWorkflowData(data);
      setWorkflowEmail(data.email);
      
      onWorkflowStatusChange?.("starting", "Starting agent...");
      
      // Step 1: Start the agent
      await startAgentMutation.mutateAsync(data);
      
      // Step 2: Enable polling for results
      setShouldPoll(true);
      
    } catch (err) {
      console.error("Submit failed:", err);
      onWorkflowStatusChange?.("error", "Failed to start agent. Please try again.");
      throw err;
    }
  };

  const isProcessing = startAgentMutation.isPending || 
                       shouldPoll || 
                       runPipelineMutation.isPending;

  const getFieldStatus = (
    fieldName: keyof FormData,
    value: string | undefined
  ) => {
    if (!touchedFields[fieldName] || !value) return null;
    if (isValidating[fieldName as "apiUrl" | "githubUrl"]) return "validating";
    if (errors[fieldName]) return "error";
    return "success";
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-7">
      <div className="space-y-3">
        <Label htmlFor="email" className="text-sm font-semibold">
          Email Address <span className="text-destructive">*</span>
        </Label>
        <div className="relative">
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            data-testid="input-email"
            className="h-12 pr-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
            {...register("email")}
          />
          {touchedFields.email && !errors.email && watch("email") && (
            <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary animate-in zoom-in duration-200" />
          )}
        </div>
        {errors.email && (
          <p className="text-xs text-destructive flex items-center gap-1.5 mt-1 animate-in slide-in-from-top-1 duration-200" data-testid="error-email">
            <AlertCircle className="h-3.5 w-3.5" />
            {errors.email.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground leading-relaxed">
          We'll send results to this address
        </p>
      </div>

      <div className="space-y-3">
        <Label htmlFor="apiUrl" className="text-sm font-semibold">
          API URL <span className="text-destructive">*</span>
        </Label>
        <div className="relative">
          <Input
            id="apiUrl"
            type="url"
            placeholder="https://api.example.com/v1"
            data-testid="input-api-url"
            className="h-12 font-mono text-sm pr-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
            {...register("apiUrl")}
            onBlur={() => handleFieldBlur("apiUrl")}
          />
          {getFieldStatus("apiUrl", apiUrlValue) === "validating" && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground animate-spin" />
          )}
          {getFieldStatus("apiUrl", apiUrlValue) === "success" && (
            <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary animate-in zoom-in duration-200" />
          )}
          {getFieldStatus("apiUrl", apiUrlValue) === "error" && (
            <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-destructive animate-in zoom-in duration-200" />
          )}
        </div>
        {errors.apiUrl && (
          <p className="text-xs text-destructive flex items-center gap-1.5 mt-1 animate-in slide-in-from-top-1 duration-200" data-testid="error-api-url">
            <AlertCircle className="h-3.5 w-3.5" />
            {errors.apiUrl.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground font-mono leading-relaxed">
          The endpoint we'll test
        </p>
      </div>

      <div className="space-y-3">
        <Label htmlFor="githubUrl" className="text-sm font-semibold">
          GitHub Repository <span className="text-destructive">*</span>
        </Label>
        <div className="relative">
          <Input
            id="githubUrl"
            type="url"
            placeholder="https://github.com/username/repo"
            data-testid="input-github-url"
            className="h-12 font-mono text-sm pr-10 transition-all duration-200 focus:ring-2 focus:ring-primary/20"
            {...register("githubUrl")}
            onBlur={() => handleFieldBlur("githubUrl")}
          />
          {getFieldStatus("githubUrl", githubUrlValue) === "validating" && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground animate-spin" />
          )}
          {getFieldStatus("githubUrl", githubUrlValue) === "success" && (
            <CheckCircle2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-primary animate-in zoom-in duration-200" />
          )}
          {getFieldStatus("githubUrl", githubUrlValue) === "error" && (
            <AlertCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-destructive animate-in zoom-in duration-200" />
          )}
        </div>
        {errors.githubUrl && (
          <p className="text-xs text-destructive flex items-center gap-1.5 mt-1 animate-in slide-in-from-top-1 duration-200" data-testid="error-github-url">
            <AlertCircle className="h-3.5 w-3.5" />
            {errors.githubUrl.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground leading-relaxed">
          Link to your API's source code for context
        </p>
      </div>

      <div className="pt-2">
        <Button
          type="submit"
          className="w-full h-12 text-base font-semibold shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all duration-200"
          disabled={isProcessing}
          data-testid="button-submit"
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Start Error Finding"
          )}
        </Button>
      </div>
    </form>
  );
}
