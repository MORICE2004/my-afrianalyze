from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext
from agents.telemetry import telemetry
import json

class TechnicalAnalysisAgent(BaseResearchAgent):
    role = AgentRole.TECHNICAL_ANALYSIS
    
    async def execute(self, context: ResearchContext) -> AgentResult:
        run_id = telemetry.start_agent_run(self.role.value)
        
        market_data = context.market_data
        
        if not market_data or "technical_indicators" not in market_data:
            telemetry.end_agent_run(run_id, status="skipped")
            return AgentResult(
                agent_role=self.role,
                success=True,
                findings=[],
                warnings=["No deterministic technical indicators found in market_data. Skipping technical reading."],
            )
            
        indicators = market_data["technical_indicators"]
        
        warnings = []
        if "rsi_14" in indicators and (indicators["rsi_14"] > 100 or indicators["rsi_14"] < 0):
            warnings.append("Invalid RSI value detected. RSI must be between 0 and 100.")
        
        if warnings:
            telemetry.end_agent_run(run_id, status="failed")
            return AgentResult(
                agent_role=self.role,
                success=False,
                findings=[],
                warnings=warnings
            )
        
        prompt = (
            f"You are the Technical Analysis Agent.\n"
            f"Review these deterministic technical indicators: {json.dumps(indicators)}\n"
            f"Synthesize the reading (bullish, bearish, neutral) and note any momentum trends.\n"
            f"DO NOT invent data. DO NOT calculate indicators yourself. Rely ONLY on the provided indicators."
        )
        
        # LLM integration (bypassed in this stub to ensure determinism/observability focus)
        # response = await self.llm_client.generate(prompt=prompt)
        # We simulate the parsed output here
        
        findings = ["Technical signals processed successfully. (Placeholder for LLM reading)"]
        
        telemetry.end_agent_run(run_id, status="success")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=findings,
            metadata={"indicators_processed": list(indicators.keys())}
        )
