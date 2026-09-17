import asyncio
import os
import sys

from packages.core.config import settings
from agents.orchestrator import ResearchOrchestrator
from agents.llm_provider import LLMClient, LLMConfig, LLMProvider

async def run_live_test():
    # Force PRODUCTION environment
    os.environ['APP_ENV'] = 'PRODUCTION'
    settings.APP_ENV = 'PRODUCTION'
    
    print("Starting LIVE NMB RESEARCH ACCEPTANCE TEST...")
    
    api_key = os.getenv('OPENAI_API_KEY', 'test_key_for_ci') 
    
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o-mini",
        api_key=api_key
    )
    llm_client = LLMClient(config)
    orchestrator = ResearchOrchestrator(llm_client)
    
    try:
        run = await orchestrator.run_research("NMB", "DSE")
        print(f"Research Run Complete: {run.id}")
        print(f"Status: {run.status}")
        print("Success.")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(run_live_test())
