import { useState } from "react";
import TestingForm from "@/components/TestingForm";
import SuccessMessage from "@/components/SuccessMessage";
import { Activity, Zap, Shield, BarChart3 } from "lucide-react";

interface SubmittedData {
  email: string;
  apiUrl: string;
  githubUrl?: string;
}

export default function Home() {
  const [submittedData, setSubmittedData] = useState<SubmittedData | null>(
    null
  );

  const handleSuccess = (data: SubmittedData) => {
    setSubmittedData(data);
  };

  const handleReset = () => {
    setSubmittedData(null);
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-background pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.1),transparent_50%)] pointer-events-none" />

      <header className="relative border-b backdrop-blur-sm bg-background/80 py-4 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-primary to-primary/80 rounded-lg p-2.5 shadow-lg shadow-primary/20">
              <Activity className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1
                className="text-2xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text"
                data-testid="text-logo"
              >
                Recompile
              </h1>
              <p className="text-xs text-muted-foreground font-medium">
                API Error Finding
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="relative flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-2xl">
          {!submittedData ? (
            <div className="space-y-10">
              <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-sm font-medium text-primary mb-4">
                  <Zap className="h-3.5 w-3.5" />
                  Enterprise-Grade Testing
                </div>
                <h2
                  className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text"
                  data-testid="text-page-title"
                >
                  Start Finding Errors
                </h2>
                <p className="text-base text-muted-foreground max-w-xl mx-auto leading-relaxed">
                  Submit your API endpoint for comprehensive error testing and analysis.
                </p>
              </div>

              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-primary/10 to-primary/20 rounded-xl blur-lg group-hover:blur-xl transition-all duration-500 opacity-50 group-hover:opacity-75" />
                <div className="relative bg-card border border-card-border rounded-xl p-10 shadow-2xl backdrop-blur-sm">
                  <TestingForm onSuccess={handleSuccess} />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-6 max-w-xl mx-auto pt-4">
                <div className="text-center space-y-2">
                  <div className="mx-auto w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Zap className="h-5 w-5 text-primary" />
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">
                    Fast Results
                  </p>
                </div>
                <div className="text-center space-y-2">
                  <div className="mx-auto w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Shield className="h-5 w-5 text-primary" />
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">
                    Secure Testing
                  </p>
                </div>
                <div className="text-center space-y-2">
                  <div className="mx-auto w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BarChart3 className="h-5 w-5 text-primary" />
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">
                    Detailed Metrics
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-primary/10 to-primary/20 rounded-xl blur-lg transition-all duration-500 opacity-50" />
              <div className="relative bg-card border border-card-border rounded-xl p-10 shadow-2xl backdrop-blur-sm">
                <SuccessMessage
                  email={submittedData.email}
                  apiUrl={submittedData.apiUrl}
                  githubUrl={submittedData.githubUrl}
                  onReset={handleReset}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
