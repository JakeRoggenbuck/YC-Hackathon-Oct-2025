from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from convex import ConvexClient
import os
from pathlib import Path
from dotenv import load_dotenv

from email_logic.startup_email import send_agent_startup_email
from email_logic.ai_pipeline import run_ai_pipeline
from moss_indexer import index_github_repo

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONVEX_URL = os.getenv("CONVEX_URL")
convex = ConvexClient(CONVEX_URL)

RUN_MOSS = False
WRITE_CONVEX = True


class StartAgentRequest(BaseModel):
    email: EmailStr
    hosted_api_url: str
    github_repo: str


class StoreResultRequest(BaseModel):
    request_id: str
    email: EmailStr
    github_url: str
    hosted_api_url: str
    result_summary: str


class RunPipelineRequest(BaseModel):
    email: EmailStr
    github_repo: str
    create_github_issues: bool = True


@app.get("/broken-route/{x}")
def broken_route(x: int):
    if x > 1000:
        # THIS IS AN ERROR!!
        raise Exception

    return "Fine"


@app.post("/start-agent")
async def start_agent(request: StartAgentRequest):
    # Create Moss index for GitHub project

    # Default value for request_id
    request_id = None

    if WRITE_CONVEX:
        mutation_result = convex.mutation(
            "agentRequests:insertRequest",
            {
                "email": request.email,
                "hostedApiUrl": request.hosted_api_url,
                "githubUrl": request.github_repo,
            },
        )
        request_id = str(mutation_result)

    if RUN_MOSS:
        index_name = await index_github_repo(request.github_repo)
        print(index_name)

    # Call email when we start indexing
    # Agent started! We'll send another email once it's complete
    send_agent_startup_email(request.email, request.hosted_api_url, request.github_repo)

    # TODO: Call our email service when it's done
    # Maybe this should be in the agent and not the backend?

    return {
        "status": "success",
        "message": "Agent started successfully",
        "requestId": request_id,
    }


@app.post("/store-result")
def store_result(request: StoreResultRequest):
    mutation_result = convex.mutation(
        "agentResults:insertResult",
        {
            "requestId": request.request_id,
            "email": request.email,
            "githubUrl": request.github_url,
            "hostedApiUrl": request.hosted_api_url,
            "resultSummary": request.result_summary,
        },
    )
    result_id = str(mutation_result)

    return {
        "status": "success",
        "message": "Result stored successfully",
        "resultId": result_id,
    }


@app.get("/get-results/{email}")
def get_results(email: str):
    results = convex.query("agentResults:getResultsByEmail", {"email": email})
    return {"status": "success", "results": results}


@app.post("/run-pipeline")
async def run_pipeline(request: RunPipelineRequest):
    """
    Run the AI pipeline on existing test results from Convex database.

    This endpoint:
    1. Fetches existing results for the email from Convex
    2. Uses the resultSummary as test results input
    3. Runs AI analysis on the test results
    4. Creates GitHub issues (if enabled)
    5. Generates and sends an email report
    """
    try:
        # Fetch existing results from Convex using the email from request body
        results_response = convex.query("agentResults:getResultsByEmail", {"email": request.email})

        if not results_response or len(results_response) == 0:
            return {
                "status": "error",
                "message": f"No results found for email: {request.email}",
                "error": "No test results available to process"
            }

        # Get the most recent result (first one in the array)
        latest_result = results_response[0]
        test_results = latest_result.get("resultSummary", "")
        hosted_api_url = latest_result.get("hostedApiUrl", "")
        github_url = latest_result.get("githubUrl", request.github_repo)

        if not test_results:
            return {
                "status": "error",
                "message": "No test results summary found in the latest result",
                "error": "resultSummary is empty or missing"
            }

        print(f"📊 Processing results for {request.email}")
        print(f"   Test results length: {len(test_results)} characters")
        print(f"   GitHub repo: {github_url}")
        print(f"   API URL: {hosted_api_url}")

        # Run the AI pipeline with the resultSummary as test_results
        pipeline_result = await run_ai_pipeline(
            test_results=test_results,
            recipient_email=request.email,
            target_repo=github_url,
            hosted_api_url=hosted_api_url,
            create_github_issues=request.create_github_issues,
        )

        print(f"✅ Pipeline completed successfully")

        return {
            "status": "success",
            "message": "Pipeline executed successfully",
            "email": request.email,
            "sourceResultId": latest_result.get("_id"),
            "githubUrl": github_url,
            "hostedApiUrl": hosted_api_url,
            "pipelineResult": {
                "issuesDetected": pipeline_result.get("issues_count", 0),
                "githubIssuesCreated": pipeline_result.get("github_issues_created", 0),
                "githubIssuesFailed": pipeline_result.get("github_issues_failed", 0),
                "emailSent": pipeline_result.get("email_sent", False),
            }
        }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Pipeline error: {error_trace}")

        return {
            "status": "error",
            "message": f"Pipeline execution failed: {str(e)}",
            "error": str(e)
        }



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
