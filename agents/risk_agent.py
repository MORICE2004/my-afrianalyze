from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class RiskAgent(BaseResearchAgent):
    role = AgentRole.RISK
    SYSTEM_PROMPT = (
        "Identify: financial risk, liquidity risk, credit risk, currency risk, governance risk,\n"
        "regulatory risk, macro risk, valuation risk, data risk.\n"
        "For each risk, assess severity and likelihood. Do NOT invent numbers.\n"
        "Reference specific evidence where possible."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Risk agent stubbed"],
        )
