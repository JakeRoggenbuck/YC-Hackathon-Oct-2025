import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

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
}

export default function TestingForm({ onSuccess }: TestingFormProps) {
  const [isValidating, setIsValidating] = useState<{
    apiUrl?: boolean;
    githubUrl?: boolean;
  }>({});

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

  const apiUrlValue = watch("apiUrl");
  const githubUrlValue = watch("githubUrl");

  const handleFieldBlur = async (field: "apiUrl" | "githubUrl") => {
    setIsValidating({ ...isValidating, [field]: true });
    await trigger(field);
    setTimeout(() => {
      setIsValidating({ ...isValidating, [field]: false });
    }, 300);
  };

  const mutation = useMutation<any, Error, FormData>({
    mutationFn: async (payload: FormData) => {
      // send form to dummy endpoint `/testing_agent`
      try {
        const res = await apiRequest("POST", "/testing_agent", payload);
        // try parse json if any
        try {
          return await res.json();
        } catch {
          return null;
        }
      } catch (err: any) {
        // If endpoint not found (404), treat as success for UI testing
        if (err && typeof err.message === "string" && err.message.startsWith("404")) {
          return null;
        }
        throw err;
      }
    },
  });

  const onSubmit = async (data: FormData) => {
    console.log("Form submitted:", data);
    try {
      await mutation.mutateAsync(data);
      if (onSuccess) onSuccess(data);
    } catch (err) {
      console.error("Submit failed:", err);
      // optionally surface error to user here
      throw err;
    }
  };

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
          disabled={isSubmitting}
          data-testid="button-submit"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : (
            "Start Error Finding"
          )}
        </Button>
      </div>
    </form>
  );
}
