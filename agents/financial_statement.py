from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class FinancialStatementAgent(BaseResearchAgent):
    role = AgentRole.FINANCIAL_STATEMENT
    SYSTEM_PROMPT = (
        "Interpret financial statements. Identify key trends, unusual items, and notable changes.\n"
        "Do NOT invent numbers. Reference specific line items from the extracted statements.\n"
        "Compare current period to prior periods. Identify one-off items."
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
