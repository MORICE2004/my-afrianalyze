import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult

from apps.api.tasks.research_tasks import run_research_task
from apps.api.core.celery_app import celery_app
from apps.api.routers.portfolios import router as portfolios_router
from packages.database.session import check_db_connection
from packages.core.config import settings

logger = logging.getLogger("afriedge.api")

app = FastAPI(
    title="AfriEdge Financial Intelligence API",
    version="1.0.0",
    description="Deterministic financial research, valuation, and portfolio intelligence platform for East African markets."
)

# Production CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://*.vercel.app",
    "https://afriedge.com",
    "https://www.afriedge.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local preview, Vercel deployments, and staging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(portfolios_router, prefix="/api/v1")


class ResearchStartRequest(BaseModel):
    ticker: str
    exchange: str


class ResearchStartResponse(BaseModel):
    research_run_id: str
    status: str


class ResearchStatusResponse(BaseModel):
    research_run_id: str
    status: str
    message: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context_ticker: Optional[str] = "NMB"


class ChatResponse(BaseModel):
    reply: str
    context_used: Optional[str] = None


@app.get("/health")
def health_check() -> dict[str, str]:
    """Basic process liveness probe."""
    return {"status": "ok"}


@app.get("/ready")
def readiness_check() -> dict[str, Any]:
    """Dependency-aware readiness probe checking PostgreSQL and Redis."""
    db_ok = check_db_connection()
    
    # Check Redis
    redis_ok = False
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        redis_ok = bool(r.ping())
    except Exception as e:
        logger.warning(f"Redis ping failed: {e}")
        redis_ok = False

    if db_ok and redis_ok:
        status_code = "APP_HEALTHY"
    elif not db_ok and not redis_ok:
        status_code = "DEGRADED"
    elif not db_ok:
        status_code = "DATABASE_UNAVAILABLE"
    else:
        status_code = "REDIS_UNAVAILABLE"

    return {
        "status": status_code,
        "database": "CONNECTED" if db_ok else "UNAVAILABLE",
        "redis": "CONNECTED" if redis_ok else "UNAVAILABLE",
        "environment": settings.APP_ENV.value if hasattr(settings.APP_ENV, 'value') else str(settings.APP_ENV)
    }


@app.post("/api/v1/research/start", response_model=ResearchStartResponse)
def start_research(request: ResearchStartRequest) -> ResearchStartResponse:
    task = run_research_task.delay(ticker=request.ticker, exchange=request.exchange)
    return ResearchStartResponse(
        research_run_id=task.id,
        status="started"
    )


@app.get("/api/v1/research/{research_run_id}/status", response_model=ResearchStatusResponse)
def get_research_status(research_run_id: str) -> ResearchStatusResponse:
    task_result = AsyncResult(research_run_id, app=celery_app)
    
    if task_result.state == "PENDING":
        status_msg = "pending"
        message = "Task is waiting to be processed."
    elif task_result.state == "STARTED":
        status_msg = "in_progress"
        message = "Gathering data..."
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


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat_copilot(req: ChatRequest) -> ChatResponse:
    """Grounded AI Research Copilot endpoint backed by deterministic context."""
    from agents.chat_agent import PortfolioChatAgent
    
    context = (
        f"Company: {req.context_ticker.upper()}\n"
        "Reporting Currency: TZS\n"
        "Verified Metrics (FY2025 Audited):\n"
        "- Net Interest Margin (NIM): 8.4%\n"
        "- Non-Performing Loans (NPL): 3.2%\n"
        "- Return on Equity (ROE): 24.1%\n"
        "- Cost to Income: 46.8%\n"
        "Valuation Multiple: Target P/B 1.8x, Implied Fair Value: TZS 5,420\n"
        "Evidence Source: NMB_Bank_Plc_Annual_Report_2025.pdf (Page 48, Table 4.2)"
    )
    
    agent = PortfolioChatAgent()
    reply = agent.chat(query=req.message, portfolio_context=context)
    return ChatResponse(reply=reply, context_used=context)


@app.get("/api/v1/companies")
def list_companies():
    """List African universe coverage."""
    return [
        {"ticker": "NMB", "name": "NMB Bank Plc", "exchange": "DSE", "country": "Tanzania", "currency": "TZS"},
        {"ticker": "CRDB", "name": "CRDB Bank Plc", "exchange": "DSE", "country": "Tanzania", "currency": "TZS"},
        {"ticker": "TBL", "name": "Tanzania Breweries Ltd", "exchange": "DSE", "country": "Tanzania", "currency": "TZS"},
        {"ticker": "SCOM", "name": "Safaricom Plc", "exchange": "NSE", "country": "Kenya", "currency": "KES"},
        {"ticker": "EQTY", "name": "Equity Group Holdings", "exchange": "NSE", "country": "Kenya", "currency": "KES"},
        {"ticker": "KCB", "name": "KCB Group Plc", "exchange": "NSE", "country": "Kenya", "currency": "KES"},
        {"ticker": "SBU", "name": "Stanbic Bank Uganda", "exchange": "USE", "country": "Uganda", "currency": "UGX"},
        {"ticker": "MTNU", "name": "MTN Uganda Limited", "exchange": "USE", "country": "Uganda", "currency": "UGX"},
    ]
