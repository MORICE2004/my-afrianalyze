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
        import json
        from agents.telemetry import telemetry
        
        run_id = telemetry.start_agent_run(self.role.value)
        
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

        # Prepare context for LLM
        prior_findings = []
        for result in context.previous_agent_results:
            for finding in result.findings:
                finding_lower = finding.lower()
                if ("compare" in finding_lower or "vs" in finding_lower or "compared" in finding_lower):
                    if ("tzs" in finding_lower and "kes" in finding_lower) and "normaliz" not in finding_lower and "convert" not in finding_lower:
                        findings.append(f"WARNING: Unnormalized cross-currency comparison detected in {result.agent_role.value}: {finding}")
                        success = False
            
            prior_findings.append({
                "agent": result.agent_role.value,
                "findings": result.findings,
                "warnings": result.warnings,
                "errors": result.errors
            })
            
        prompt = (
            f"Review the following research findings:\n{json.dumps(prior_findings, indent=2)}\n\n"
            f"Apply your adversarial checklist to identify any hidden risks, inconsistencies, or analytical errors.\n"
            f"If there are major issues, explain them."
        )
        
        try:
            llm_response = await self.llm_client.generate(prompt=prompt, system_prompt=self.SYSTEM_PROMPT)
            findings.append(f"Auditor LLM Review:\n{llm_response}")
        except Exception as e:
            findings.append(f"Auditor LLM call failed: {str(e)}")
            success = False

        if not findings:
            findings.append("No material issues found.")

        telemetry.end_agent_run(run_id, status="success" if success else "failed")

        return AgentResult(
            agent_role=self.role,
            success=success,
            findings=findings,
        )
