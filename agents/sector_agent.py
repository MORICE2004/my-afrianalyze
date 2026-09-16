from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class SectorAgent(BaseResearchAgent):
    role = AgentRole.SECTOR
    SYSTEM_PROMPT = (
        "Analyze industry structure, competition, sector economics, sector-specific KPIs.\n"
        "For banks: focus on banking sector structure, regulatory environment, competitive dynamics.\n"
        "For telecom: subscriber metrics, ARPU, spectrum. Etc."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Sector agent stubbed"],
        )
