from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class ResearchDirectorAgent(BaseResearchAgent):
    role = AgentRole.RESEARCH_DIRECTOR
    SYSTEM_PROMPT = (
        "You are the Research Director. Consolidate all verified outputs into the final research report.\n"
        "Structure: Company overview, Investment thesis, Industry analysis, Macro, Management, Financial analysis,\n"
        "Historical performance, Ratios, Earnings quality, Balance sheet, Cash flow, Peers, Market performance,\n"
        "Beta, Forecasts, Scenarios, Valuation, Sensitivity, Risks, Catalysts, What could invalidate the thesis,\n"
        "Final Buy/Hold/Sell assessment, Data quality, Sources, Calculation appendix.\n"
        "Use ONLY verified data from other agents. Never invent numbers.\n"
        "If the auditor flagged material issues, acknowledge them prominently."
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
