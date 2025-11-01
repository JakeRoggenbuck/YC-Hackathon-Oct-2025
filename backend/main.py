from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from email_logic.startup_email import send_agent_startup_email
from moss_indexer import index_github_repo

app = FastAPI()


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
        "data": {
            "email": request.email,
            "hosted_api_url": request.hosted_api_url,
            "github_repo": request.github_repo
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
