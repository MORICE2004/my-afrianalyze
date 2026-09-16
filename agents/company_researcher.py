from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class CompanyResearcherAgent(BaseResearchAgent):
    role = AgentRole.COMPANY_RESEARCHER
    SYSTEM_PROMPT = (
        "Research: business model, products, segments, management, ownership, strategy, competitive position.\n"
        "You are analyzing an African public company. Focus on publicly available information.\n"
        "Do NOT invent facts. Cite sources for every claim.\n"
        "Output structured findings about the company."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Company research agent not yet connected to live data"],
        )
