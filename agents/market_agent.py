from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class MarketAgent(BaseResearchAgent):
    role = AgentRole.MARKET
    SYSTEM_PROMPT = (
        "Analyze share price performance, returns, volume, liquidity, beta, market cap.\n"
        "Use the deterministic beta and market data already computed. Interpret the results.\n"
        "Explicitly note if the security is illiquid or if data is sparse."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        from agents.telemetry import telemetry
        import json
        run_id = telemetry.start_agent_run(self.role.value)
        
        prompt = f"Analyze the following data context:\n{json.dumps(context.model_dump(), default=str)[:2000]}..."
        
        try:
            llm_response = await self.llm_client.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
            findings = [f"{self.role.value} LLM analysis:\n{llm_response}"]
            success = True
        except Exception as e:
            findings = [f"LLM call failed: {str(e)}"]
            success = False
            
        telemetry.end_agent_run(run_id, status="success" if success else "failed")
        
        return AgentResult(
            agent_role=self.role,
            success=success,
            findings=findings,
        )
