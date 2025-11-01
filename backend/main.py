from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from convex import ConvexClient
import os
from pathlib import Path
from dotenv import load_dotenv

from email_logic.startup_email import send_agent_startup_email
from moss_indexer import index_github_repo

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI()

CONVEX_URL = os.getenv("CONVEX_URL")
convex = ConvexClient(CONVEX_URL)

RUN_MOSS = False
WRITE_CONVEX = True


class StartAgentRequest(BaseModel):
    email: EmailStr
    hosted_api_url: str
    github_repo: str


@app.get("/broken-route/{x}")
def broken_route(x: int):
    if x > 1000:
        # THIS IS AN ERROR!!
        raise Exception

    return "Fine"


@app.post("/start-agent")
async def start_agent(request: StartAgentRequest):
    # Create Moss index for GitHub project

    # Default value for request
    request_id = request

    if WRITE_CONVEX:
        request_id = convex.mutation(
            "agentRequests:insertRequest",
            {
                "email": request.email,
                "hostedApiUrl": request.hosted_api_url,
                "githubUrl": request.github_repo,
            },
        )

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
