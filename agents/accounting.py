from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class AccountingAgent(BaseResearchAgent):
    role = AgentRole.ACCOUNTING
    SYSTEM_PROMPT = (
        "Check accounting consistency, restatements, classification changes, one-off items, earnings quality.\n"
        "Use the deterministic validation results already computed. Do NOT recalculate.\n"
        "Flag any concerns about earnings quality or accounting choices."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Accounting agent stubbed"],
        )
