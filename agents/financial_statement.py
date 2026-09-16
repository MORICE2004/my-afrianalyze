from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class FinancialStatementAgent(BaseResearchAgent):
    role = AgentRole.FINANCIAL_STATEMENT
    SYSTEM_PROMPT = (
        "Interpret financial statements. Identify key trends, unusual items, and notable changes.\n"
        "Do NOT invent numbers. Reference specific line items from the extracted statements.\n"
        "Compare current period to prior periods. Identify one-off items."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Financial statement agent stubbed"],
        )
