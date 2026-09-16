from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class ScenarioAgent(BaseResearchAgent):
    role = AgentRole.SCENARIO
    SYSTEM_PROMPT = (
        "Interpret Bear/Base/Bull assumptions and sensitivity analysis.\n"
        "Explain the economic reasoning behind each scenario.\n"
        "Identify which assumptions are most sensitive.\n"
        "Do NOT modify the deterministic scenario calculations."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Scenario agent stubbed"],
        )
