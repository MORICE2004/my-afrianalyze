from fastapi import FastAPI
from pydantic import BaseModel
import uuid

class ResearchStartRequest(BaseModel):
    ticker: str
    exchange: str

class ResearchStartResponse(BaseModel):
    research_run_id: str
    status: str

class ResearchStatusResponse(BaseModel):
    research_run_id: str
    status: str
    message: str | None = None

app = FastAPI(title="My AfriAnalyze API")

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/v1/research/start", response_model=ResearchStartResponse)
def start_research(request: ResearchStartRequest) -> ResearchStartResponse:
    run_id = str(uuid.uuid4())
    return ResearchStartResponse(
        research_run_id=run_id,
        status="started"
    )

@app.get("/api/v1/research/{research_run_id}/status", response_model=ResearchStatusResponse)
def get_research_status(research_run_id: str) -> ResearchStatusResponse:
    return ResearchStatusResponse(
        research_run_id=research_run_id,
        status="in_progress",
        message="Gathering data..."
    )
