import pytest
from agents.auditor import AuditorAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent
from agents.synthesis import SynthesisAgent
from agents.base import ResearchContext, AgentResult, AgentRole

@pytest.mark.asyncio
async def test_auditor_flags_mismatched_currencies():
    auditor = AuditorAgent(llm_client=None)
    
    context = ResearchContext(
        financial_data={
            "currency": "KES",
            "balance_sheet": {"total_assets": 1000},
        },
        market_data={
            "currency": "USD",
            "price": 10.0
        }
    )
    
    result = await auditor.execute(context)
    assert not result.success
    assert any("currency" in finding.lower() for finding in result.findings)

@pytest.mark.asyncio
async def test_auditor_flags_math_error_in_balance_sheet():
    auditor = AuditorAgent(llm_client=None)
    
    context = ResearchContext(
        financial_data={
            "currency": "KES",
            "balance_sheet": {
                "total_assets": 1000,
                "total_liabilities": 800,
                "total_equity": 150
            },
        },
        market_data={
            "currency": "KES",
            "price": 10.0
        }
    )
    
    result = await auditor.execute(context)
    assert not result.success
    assert any("balance sheet" in finding.lower() for finding in result.findings)

@pytest.mark.asyncio
async def test_technical_analysis_flags_fake_indicators():
    ta_agent = TechnicalAnalysisAgent(llm_client=None)
    
    # Fake technical indicator: current price is 10, but 50-day SMA is impossibly high
    context = ResearchContext(
        financial_data={},
        market_data={
            "price": 10.0,
            "technical_indicators": {
                "sma_50": 9000.0,
                "rsi_14": 150.0  # RSI > 100 is mathematically impossible
            }
        }
    )
    
    result = await ta_agent.execute(context)
    # The TA agent (or stub) should ideally catch this. 
    # For now, let's assume the agent result includes a warning or fails.
    # To pass, we expect the test to check if the agent notices the impossible RSI.
    # We will adjust the TA agent stub to actually throw a warning if RSI > 100.
    assert "rsi" in str(result.warnings).lower() or not result.success

@pytest.mark.asyncio
async def test_synthesis_flags_lookahead_bias():
    synthesis_agent = SynthesisAgent(llm_client=None)
    
    # Look-ahead bias: Using Q4 data while we are in Q3
    context = ResearchContext(
        financial_data={},
        market_data={},
        previous_agent_results=[
            AgentResult(
                agent_role=AgentRole.VALUATION,
                success=True,
                findings=["DCF Valuation based on Q4 actuals (which haven't happened yet)"]
            ),
            AgentResult(
                agent_role=AgentRole.TECHNICAL_ANALYSIS,
                success=True,
                findings=["Technical signals show bullish trend"]
            )
        ]
    )
    
    result = await synthesis_agent.execute(context)
    # Synthesis agent should detect contradiction or lookahead bias
    assert "lookahead" in str(result.warnings).lower() or not result.success
