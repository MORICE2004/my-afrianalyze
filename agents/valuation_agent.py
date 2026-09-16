from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class ValuationAgent(BaseResearchAgent):
    role = AgentRole.VALUATION
    SYSTEM_PROMPT = (
        "Interpret the deterministic valuation output. Do NOT recalculate.\n"
        "Explain what the valuation models suggest about fair value.\n"
        "Compare different models and explain discrepancies.\n"
        "Note the key assumptions driving the valuation."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Valuation agent stubbed"],
        )
