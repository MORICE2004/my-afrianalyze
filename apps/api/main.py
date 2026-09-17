from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apps.api.tasks.research_tasks import run_research_task
from apps.api.core.celery_app import celery_app

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
    task = run_research_task.delay(ticker=request.ticker, exchange=request.exchange)
    return ResearchStartResponse(
        research_run_id=task.id,
        status="started"
    )

@app.get("/api/v1/research/{research_run_id}/status", response_model=ResearchStatusResponse)
def get_research_status(research_run_id: str) -> ResearchStatusResponse:
    task_result = celery_app.AsyncResult(research_run_id)
    
    if task_result.state == "PENDING":
        status_msg = "pending"
        message = "Task is waiting to be processed."
    elif task_result.state == "STARTED":
        status_msg = "in_progress"
        message = "Research is currently running."
    elif task_result.state == "SUCCESS":
        status_msg = "completed"
        message = "Research finished successfully."
    elif task_result.state == "FAILURE":
        status_msg = "failed"
        message = str(task_result.info)
    else:
        status_msg = task_result.state.lower()
        message = "Research is progressing."
        
    return ResearchStatusResponse(
        research_run_id=research_run_id,
        status=status_msg,
        message=message
    )
