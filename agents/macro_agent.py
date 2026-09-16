from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class MacroAgent(BaseResearchAgent):
    role = AgentRole.MACRO
    SYSTEM_PROMPT = (
        "Analyze macroeconomic environment: inflation, interest rates, GDP, currency, policy, commodity exposure, country risk.\n"
        "Focus on the specific African country where the company operates.\n"
        "Use publicly available data. Cite sources."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Macro agent stubbed"],
        )
