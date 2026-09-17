from typing import Dict, Any, List
from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext
from packages.currency.engine import CurrencyEngine

class SectorAgent(BaseResearchAgent):
    role = AgentRole.SECTOR
    SYSTEM_PROMPT = (
        "Analyze industry structure, competition, sector economics, sector-specific KPIs.\n"
        "For banks: focus on banking sector structure, regulatory environment, competitive dynamics.\n"
        "For telecom: subscriber metrics, ARPU, spectrum. Etc."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        from agents.telemetry import telemetry
        import json
        run_id = telemetry.start_agent_run(self.role.value)
        
        # Implement cross-market peer comparison if peers are provided
        peer_comparison_data = []
        if getattr(context, 'peers', None):
            for peer in context.peers:
                # E.g. peer might have 'currency' and 'market_cap'
                peer_currency = peer.get('currency', 'USD')
                market_cap = peer.get('market_cap')
                
                if market_cap and peer_currency != 'USD':
                    # We need a mock fx_rate for this example or fetch it
                    # Let's use some hardcoded test rates for demonstration
                    from packages.core.config import settings
                    from packages.core.exceptions import ProductionDataViolation
                    if settings.APP_ENV == "PRODUCTION":
                        raise ProductionDataViolation("Mock reached in production")
                    fx_rates = {
                        'TZS': 1/2500,
                        'KES': 1/130,
                        'UGX': 1/3800
                    }
                    rate = fx_rates.get(peer_currency, 1.0)
                    converted = CurrencyEngine.convert(
                        value=market_cap,
                        from_currency=peer_currency,
                        to_currency='USD',
                        fx_rate=rate,
                        fx_date=None,
                        fx_source='CrossMarketFX'
                    )
                    normalized_cap = converted.normalized_value if converted else market_cap
                else:
                    normalized_cap = market_cap
                    
                peer_comparison_data.append({
                    'ticker': peer.get('ticker'),
                    'exchange': peer.get('exchange'),
                    'original_market_cap': market_cap,
                    'original_currency': peer_currency,
                    'normalized_market_cap_usd': normalized_cap
                })
        
        prompt_data = context.model_dump()
        prompt_data['cross_market_peers'] = peer_comparison_data
        prompt = f"Analyze the following data context with cross-market peers:\n{json.dumps(prompt_data, default=str)[:3000]}..."
        
        try:
            llm_response = await self.llm_client.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
            findings = [f"{self.role.value} LLM analysis:\n{llm_response}"]
            if peer_comparison_data:
                findings.append(f"Cross-Market Peer Data: {json.dumps(peer_comparison_data)}")
            success = True
        except Exception as e:
            findings = [f"LLM call failed: {str(e)}"]
            success = False
            
        telemetry.end_agent_run(run_id, status="success" if success else "failed")
        
        return AgentResult(
            agent_role=self.role,
            success=success,
            findings=findings,
        )
