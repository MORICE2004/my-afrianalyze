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
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Research director agent stubbed"],
        )
