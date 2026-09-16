from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class MarketAgent(BaseResearchAgent):
    role = AgentRole.MARKET
    SYSTEM_PROMPT = (
        "Analyze share price performance, returns, volume, liquidity, beta, market cap.\n"
        "Use the deterministic beta and market data already computed. Interpret the results.\n"
        "Explicitly note if the security is illiquid or if data is sparse."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Market agent stubbed"],
        )
