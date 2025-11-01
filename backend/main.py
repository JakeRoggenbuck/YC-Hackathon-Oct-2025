from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()


class StartAgentRequest(BaseModel):
    email: EmailStr
    hosted_api_url: str
    github_repo: str


@app.get("/broken-route/{x}")
def broken_route(x: int):
    if x > 1000:
        raise Exception

    return "Fine"


@app.post("/start-agent")
def start_agent(request: StartAgentRequest):

    # TODO: Start and agent that is on stand-by

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
