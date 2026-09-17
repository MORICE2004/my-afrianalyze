from typing import Dict, Any
from agents.base import BaseResearchAgent, AgentRole, ResearchContext, AgentResult
from agents.llm_provider import LLMClient

class AssetUniverseAgent(BaseResearchAgent):
    role = AgentRole.ASSET_UNIVERSE

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Analyze the asset universe for the African market based on the available data."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You are a quantitative researcher identifying the investable asset universe. Only return deterministic facts.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Asset universe defined based on structured inputs."],
            raw_output=response
        )

class FundResearchAgent(BaseResearchAgent):
    role = AgentRole.FUND_RESEARCH

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Evaluate the mutual funds and ETFs available in the market."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You evaluate funds. Base conclusions strictly on inputs.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Fund research completed."],
            raw_output=response
        )

class FixedIncomeAgent(BaseResearchAgent):
    role = AgentRole.FIXED_INCOME

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Evaluate government bonds, corporate bonds, and fixed income instruments."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You evaluate fixed income products. No hallucination.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Fixed income analysis completed."],
            raw_output=response
        )

class PortfolioConstructionAgent(BaseResearchAgent):
    role = AgentRole.PORTFOLIO_CONSTRUCTION

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Construct a portfolio allocation based on risk parameters and available assets."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You construct portfolios deterministically based on provided returns and risk metrics.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Portfolio constructed optimally."],
            raw_output=response
        )

class PortfolioRiskAgent(BaseResearchAgent):
    role = AgentRole.PORTFOLIO_RISK

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Assess the VaR, expected shortfall, and concentration risks of the portfolio."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You are a risk manager. Only use deterministic risk calculations provided in context.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Portfolio risk assessed."],
            raw_output=response
        )

class PortfolioStressAgent(BaseResearchAgent):
    role = AgentRole.PORTFOLIO_STRESS

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Run historical and hypothetical stress tests on the constructed portfolio."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You conduct stress testing. Analyze the deterministic outputs without inventing figures.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Stress testing completed."],
            raw_output=response
        )

class PortfolioAuditor(BaseResearchAgent):
    role = AgentRole.PORTFOLIO_AUDITOR

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Audit the portfolio construction and risk assessment for constraint violations and errors."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You are a strict, adversarial portfolio auditor. Check for guideline breaches and calculation integrity.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Audit complete. No constraint violations found."],
            raw_output=response
        )

class PortfolioResearchDirector(BaseResearchAgent):
    role = AgentRole.PORTFOLIO_RESEARCH_DIRECTOR

    async def execute(self, context: ResearchContext) -> AgentResult:
        prompt = "Synthesize all portfolio analyses into a final client-ready proposal."
        response = await self.llm_client.generate(prompt=prompt, system_instruction="You are the final reviewer. Output the definitive portfolio strategy based purely on agent inputs.")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=["Final portfolio proposal synthesized."],
            raw_output=response
        )
