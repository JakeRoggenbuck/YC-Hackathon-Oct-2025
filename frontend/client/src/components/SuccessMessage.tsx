import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface SuccessMessageProps {
  email: string;
  apiUrl: string;
  githubUrl?: string;
  onReset: () => void;
}

export default function SuccessMessage({
  email,
  apiUrl,
  githubUrl,
  onReset,
}: SuccessMessageProps) {
  const obscureEmail = (email: string) => {
    const [localPart, domain] = email.split("@");
    const obscured = localPart.charAt(0) + "***" + localPart.slice(-1);
    return `${obscured}@${domain}`;
  };

  return (
    <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500">
      <div className="flex flex-col items-center text-center space-y-5">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse" />
          <div className="relative rounded-full bg-gradient-to-br from-primary/20 to-primary/10 p-5 ring-1 ring-primary/30">
            <CheckCircle2 className="h-14 w-14 text-primary" data-testid="icon-success" />
          </div>
        </div>
        <div className="space-y-3">
          <h2 className="text-3xl font-bold tracking-tight" data-testid="text-success-title">
            Testing Request Submitted
          </h2>
          <p className="text-base text-muted-foreground max-w-md leading-relaxed">
            We're now processing your API testing request. You'll receive detailed
            results at your email address.
          </p>
        </div>
      </div>

      <Card className="p-8 space-y-5 shadow-lg">
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
          Submission Details
        </h3>
        <div className="space-y-4">
          <div className="space-y-2 pb-4 border-b">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</p>
            <p className="font-mono text-sm" data-testid="text-submitted-email">
              {obscureEmail(email)}
            </p>
          </div>
          <div className="space-y-2 pb-4 border-b">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">API Endpoint</p>
            <p className="font-mono text-sm break-all" data-testid="text-submitted-api-url">
              {apiUrl}
            </p>
          </div>
          {githubUrl && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">GitHub Repository</p>
              <p className="font-mono text-sm break-all" data-testid="text-submitted-github-url">
                {githubUrl}
              </p>
            </div>
          )}
        </div>
      </Card>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold">What happens next?</h3>
        <ul className="space-y-3 text-sm text-muted-foreground">
          <li className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <span className="text-primary font-mono text-sm font-bold mt-0.5 bg-primary/10 px-2 py-0.5 rounded">01</span>
            <span className="leading-relaxed">Your API will be queued</span>
          </li>
          <li className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <span className="text-primary font-mono text-sm font-bold mt-0.5 bg-primary/10 px-2 py-0.5 rounded">02</span>
            <span className="leading-relaxed">We'll run comprehensive testing</span>
          </li>
          <li className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
            <span className="text-primary font-mono text-sm font-bold mt-0.5 bg-primary/10 px-2 py-0.5 rounded">03</span>
            <span className="leading-relaxed">Detailed results will be emailed</span>
          </li>
        </ul>
      </div>

      <Button
        variant="outline"
        className="w-full h-12 font-semibold"
        onClick={onReset}
        data-testid="button-submit-another"
      >
        Submit Another Request
      </Button>
    </div>
  );
}
