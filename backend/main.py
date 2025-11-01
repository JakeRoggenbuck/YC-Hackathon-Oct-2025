from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class StartAgentRequest(BaseModel):
    email: EmailStr
    hosted_api_url: str
    github_repo: str


@app.post("/start-agent")
def start_agent(request: StartAgentRequest):
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
