import asyncio
import os
from celery import shared_task
from agents.orchestrator import ResearchOrchestrator
from agents.llm_provider import LLMClient

@shared_task(bind=True, name="research_tasks.run_research_task")
def run_research_task(self, ticker: str, exchange: str):
    # Setup LLMClient
    llm_client = LLMClient(
        provider="dummy",  # In real life, get from config
        api_key="dummy_key"
    )
    
    orchestrator = ResearchOrchestrator(llm_client=llm_client)
    
    # Run the orchestrator in an event loop
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        run_result = loop.run_until_complete(orchestrator.run_research(ticker, exchange))
        return {
            "status": run_result.state.value,
            "run_id": str(run_result.run_id),
            "ticker": ticker,
            "exchange": exchange
        }
    except Exception as e:
        self.update_state(state="FAILURE", meta={"exc_type": type(e).__name__, "exc_message": str(e)})
        raise e
