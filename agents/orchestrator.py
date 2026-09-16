import enum
from typing import Dict, List
from uuid import uuid4

from agents.llm_provider import LLMClient
from agents.base import AgentRole, BaseResearchAgent, ResearchContext

from agents.company_researcher import CompanyResearcherAgent
from agents.financial_statement import FinancialStatementAgent
from agents.accounting import AccountingAgent
from agents.market_agent import MarketAgent
from agents.macro_agent import MacroAgent
from agents.sector_agent import SectorAgent
from agents.valuation_agent import ValuationAgent
from agents.risk_agent import RiskAgent
from agents.scenario_agent import ScenarioAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent
from agents.synthesis import SynthesisAgent
from agents.auditor import AuditorAgent
from agents.research_director import ResearchDirectorAgent

class ResearchRunState(enum.Enum):
    PENDING = "PENDING"
    DISCOVERING = "DISCOVERING"
    ACCOUNTING_CHECK = "ACCOUNTING_CHECK"
    VALUING = "VALUING"
    SCENARIO_RISK = "SCENARIO_RISK"
    TECHNICAL_SYNTHESIS = "TECHNICAL_SYNTHESIS"
    AUDITING = "AUDITING"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ResearchRun:
    def __init__(self, ticker: str, exchange: str):
        self.run_id = uuid4()
        self.ticker = ticker
        self.exchange = exchange
        self.state = ResearchRunState.PENDING
        self.context = ResearchContext(research_run_id=self.run_id)

class ResearchOrchestrator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.agents: Dict[AgentRole, BaseResearchAgent] = {
            AgentRole.COMPANY_RESEARCHER: CompanyResearcherAgent(llm_client),
            AgentRole.FINANCIAL_STATEMENT: FinancialStatementAgent(llm_client),
            AgentRole.ACCOUNTING: AccountingAgent(llm_client),
            AgentRole.MARKET: MarketAgent(llm_client),
            AgentRole.MACRO: MacroAgent(llm_client),
            AgentRole.SECTOR: SectorAgent(llm_client),
            AgentRole.VALUATION: ValuationAgent(llm_client),
            AgentRole.RISK: RiskAgent(llm_client),
            AgentRole.SCENARIO: ScenarioAgent(llm_client),
            AgentRole.TECHNICAL_ANALYSIS: TechnicalAnalysisAgent(llm_client),
            AgentRole.SYNTHESIS: SynthesisAgent(llm_client),
            AgentRole.AUDITOR: AuditorAgent(llm_client),
            AgentRole.RESEARCH_DIRECTOR: ResearchDirectorAgent(llm_client),
        }

    async def run_research(self, company_ticker: str, exchange: str) -> ResearchRun:
        run = ResearchRun(ticker=company_ticker, exchange=exchange)
        
        try:
            # Phase 1: Parallel (Discovery)
            run.state = ResearchRunState.DISCOVERING
            phase1_roles = [
                AgentRole.COMPANY_RESEARCHER, AgentRole.FINANCIAL_STATEMENT, 
                AgentRole.MARKET, AgentRole.MACRO, AgentRole.SECTOR
            ]
            for role in phase1_roles:
                result = await self.agents[role].execute(run.context)
                run.context.previous_agent_results.append(result)

            # Phase 2: Sequential (Accounting)
            run.state = ResearchRunState.ACCOUNTING_CHECK
            result = await self.agents[AgentRole.ACCOUNTING].execute(run.context)
            run.context.previous_agent_results.append(result)

            # Phase 3: Sequential (Valuation)
            run.state = ResearchRunState.VALUING
            # Check critical data gates before valuation (stubbed)
            if not run.context.financial_data and False: # Stub for gate check
                raise ValueError("Missing critical financial data for valuation.")
            
            result = await self.agents[AgentRole.VALUATION].execute(run.context)
            run.context.previous_agent_results.append(result)

            # Phase 4: Sequential (Scenario & Risk)
            run.state = ResearchRunState.SCENARIO_RISK
            for role in [AgentRole.SCENARIO, AgentRole.RISK]:
                result = await self.agents[role].execute(run.context)
                run.context.previous_agent_results.append(result)

            # Phase 4.5: Technical Analysis and Synthesis
            run.state = ResearchRunState.TECHNICAL_SYNTHESIS
            for role in [AgentRole.TECHNICAL_ANALYSIS, AgentRole.SYNTHESIS]:
                result = await self.agents[role].execute(run.context)
                run.context.previous_agent_results.append(result)

            # Phase 5: Sequential (Auditor)
            run.state = ResearchRunState.AUDITING
            result = await self.agents[AgentRole.AUDITOR].execute(run.context)
            run.context.previous_agent_results.append(result)

            # Phase 6: Sequential (Director)
            run.state = ResearchRunState.FINALIZING
            result = await self.agents[AgentRole.RESEARCH_DIRECTOR].execute(run.context)
            run.context.previous_agent_results.append(result)

            run.state = ResearchRunState.COMPLETED
            
        except Exception as e:
            run.state = ResearchRunState.FAILED
            # Add basic exception handling/logging as needed
            
        return run
