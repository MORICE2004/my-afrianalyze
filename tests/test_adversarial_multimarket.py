import pytest

pytest.importorskip("litellm", reason="legacy LLM agent layer (agents/) needs litellm, which is not installed; the AI layer is off for v1 (docs/KNOWN_GAPS.md)")

from agents.auditor import AuditorAgent
from agents.base import ResearchContext, AgentResult, AgentRole

@pytest.mark.asyncio
async def test_auditor_flags_unnormalized_cross_currency():
    """
    Simulates a SectorAgent output comparing TZS to KES without normalizing the currency,
    and ensures the AuditorAgent flags it.
    """
    auditor = AuditorAgent(llm_client=None)
    
    # Fake SectorAgent result
    sector_result = AgentResult(
        agent_role=AgentRole.SECTOR,
        success=True,
        findings=[
            "Compared CRDB (TZS) to KCB (KES). CRDB has higher assets."
        ]
    )
    
    context = ResearchContext(
        financial_data={"currency": "TZS"},
        market_data={"currency": "TZS"},
        previous_agent_results=[sector_result]
    )
    
    result = await auditor.execute(context)
    
    assert not result.success
    assert any("warning" in finding.lower() and "unnormalized" in finding.lower() for finding in result.findings)
