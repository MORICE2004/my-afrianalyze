import os
import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelemetryManager:
    """
    Observability layer for AfriAnalyze.
    Manages Run IDs, Cost tracking, and execution tracing.
    """
    def __init__(self):
        self.run_id = str(uuid.uuid4())
        self.metrics = {
            "total_cost": 0.0,
            "total_tokens": 0,
            "agents_executed": [],
            "start_time": datetime.utcnow().isoformat()
        }

    def start_agent_run(self, agent_name: str) -> str:
        execution_id = str(uuid.uuid4())
        self.metrics["agents_executed"].append({
            "agent_name": agent_name,
            "execution_id": execution_id,
            "start_time": time.time(),
            "status": "running"
        })
        logger.info(f"[{self.run_id}] Agent {agent_name} started (Execution ID: {execution_id})")
        return execution_id

    def end_agent_run(self, execution_id: str, status: str = "success", cost: float = 0.0):
        for run in self.metrics["agents_executed"]:
            if run["execution_id"] == execution_id:
                run["status"] = status
                run["end_time"] = time.time()
                run["duration"] = run["end_time"] - run["start_time"]
                run["cost"] = cost
                logger.info(f"[{self.run_id}] Agent {run['agent_name']} ended with status {status}. Duration: {run['duration']:.2f}s. Cost: ${cost:.6f}")
                break

    def log_llm_cost(self, provider: str, model_name: str, tokens: int, estimated_cost: float):
        self.metrics["total_cost"] += estimated_cost
        self.metrics["total_tokens"] += tokens
        logger.debug(f"LLM call to {provider}/{model_name} used {tokens} tokens. Cost: ${estimated_cost:.6f}")

    def get_summary(self) -> Dict[str, Any]:
        return self.metrics

telemetry = TelemetryManager()
