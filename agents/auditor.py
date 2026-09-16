from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext

class AuditorAgent(BaseResearchAgent):
    role = AgentRole.AUDITOR
    SYSTEM_PROMPT = (
        "You are the adversarial auditor. Your job is to CHALLENGE the research.\n"
        "Ask and answer these questions:\n"
        "1. Is each material number sourced?\n"
        "2. Are currencies consistent?\n"
        "3. Are reporting periods consistent?\n"
        "4. Are standalone and consolidated values mixed?\n"
        "5. Are calculations mathematically correct?\n"
        "6. Does the balance sheet reconcile?\n"
        "7. Are forecasts using information available at the forecast date?\n"
        "8. Are assumptions internally consistent?\n"
        "9. Are comparable companies genuinely comparable?\n"
        "10. Is the valuation model appropriate for the sector?\n"
        "11. Could illiquidity distort beta?\n"
        "12. Could FX distort historical growth?\n"
        "13. Could accounting changes distort trends?\n"
        "14. Are one-off gains treated as recurring earnings?\n"
        "15. Are there conflicting company disclosures?\n"
        "16. Is the current market price stale?\n"
        "Flag ALL unresolved issues. Do NOT approve the research if material issues exist."
    )

    async def execute(self, context: ResearchContext) -> AgentResult:
        findings = []
        success = True
        
        # Check currency consistency
        fin_currency = context.financial_data.get("currency")
        mkt_currency = context.market_data.get("currency")
        
        if fin_currency and mkt_currency and fin_currency != mkt_currency:
            findings.append(f"Currency mismatch: Financials in {fin_currency}, Market data in {mkt_currency}")
            success = False
            
        # Check balance sheet reconciliation
        bs = context.financial_data.get("balance_sheet", {})
        assets = bs.get("total_assets")
        liabilities = bs.get("total_liabilities")
        equity = bs.get("total_equity")
        
        if assets is not None and liabilities is not None and equity is not None:
            if abs(assets - (liabilities + equity)) > 0.01:
                findings.append(f"Balance sheet does not reconcile: Assets ({assets}) != Liabilities ({liabilities}) + Equity ({equity})")
                success = False

        if not findings:
            findings.append("No material issues found.")

        return AgentResult(
            agent_role=self.role,
            success=success,
            findings=findings,
        )
