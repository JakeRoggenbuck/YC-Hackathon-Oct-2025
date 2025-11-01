import { Loader2, CheckCircle2, Clock, Rocket, Search, Mail } from "lucide-react";
import { Card } from "@/components/ui/card";

interface WorkflowProgressProps {
  status: string;
  message?: string;
}

export default function WorkflowProgress({ status, message }: WorkflowProgressProps) {
  const steps = [
    {
      id: "starting",
      label: "Starting Agent",
      icon: Rocket,
      description: "Initializing testing agent...",
    },
    {
      id: "waiting-for-results",
      label: "Running Tests",
      icon: Search,
      description: "Testing your API endpoints...",
    },
    {
      id: "running-pipeline",
      label: "Analyzing Results",
      icon: Clock,
      description: "AI is analyzing test results and creating issues...",
    },
    {
      id: "complete",
      label: "Complete",
      icon: Mail,
      description: "Results sent to your email!",
    },
  ];

  const getStepStatus = (stepId: string) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    const currentIndex = steps.findIndex(s => s.id === status);
    
    if (currentIndex < 0) return "pending";
    if (stepIndex < currentIndex) return "complete";
    if (stepIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <Card className="p-8 space-y-6">
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">Processing Your Request</h3>
        {message && (
          <p className="text-sm text-muted-foreground">{message}</p>
        )}
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.id);
          const Icon = step.icon;
          
          return (
            <div key={step.id} className="flex items-start gap-4">
              <div className="relative flex-shrink-0">
                <div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
                    ${stepStatus === "complete" 
                      ? "bg-primary text-primary-foreground" 
                      : stepStatus === "active"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                    }
                  `}
                >
                  {stepStatus === "complete" ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : stepStatus === "active" ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Icon className="h-5 w-5" />
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`
                      absolute left-5 top-10 w-0.5 h-8 transition-all duration-300
                      ${stepStatus === "complete" ? "bg-primary" : "bg-muted"}
                    `}
                  />
                )}
              </div>

              <div className="flex-1 pt-1.5">
                <div
                  className={`
                    font-medium transition-all duration-300
                    ${stepStatus === "active" ? "text-primary" : ""}
                  `}
                >
                  {step.label}
                </div>
                <div className="text-sm text-muted-foreground mt-0.5">
                  {step.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {status === "error" && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-sm text-destructive font-medium">
            {message || "An error occurred. Please try again."}
          </p>
        </div>
      )}
    </Card>
  );
}
