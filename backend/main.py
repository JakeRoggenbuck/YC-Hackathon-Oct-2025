from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from convex import ConvexClient
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

app = FastAPI()

CONVEX_URL = os.getenv("CONVEX_URL")
convex = ConvexClient(CONVEX_URL)

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
def start_agent(request: StartAgentRequest):

    request_id = convex.mutation("agentRequests:insertRequest",
                {
                    "email": request.email,
                    "hosted_api_url": request.hosted_api_url,
                    "github_repo": request.github_repo
                })

    # TODO: Call our email service when it's done
    # Maybe this should be in the agent and not the backend?

    return {
        "status": "success",
        "message": "Agent started successfully",
        "requestId": request_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
