from agents.base import BaseResearchAgent, AgentRole, AgentResult, ResearchContext
from agents.telemetry import telemetry
import json

class SynthesisAgent(BaseResearchAgent):
    role = AgentRole.SYNTHESIS
    
    async def execute(self, context: ResearchContext) -> AgentResult:
        run_id = telemetry.start_agent_run(self.role.value)
        
        # Gather previous results from fundamental valuation vs technical analysis
        fundamental_findings = []
        technical_findings = []
        
        for result in context.previous_agent_results:
            if result.agent_role == AgentRole.VALUATION:
                fundamental_findings.extend(result.findings)
            elif result.agent_role == AgentRole.TECHNICAL_ANALYSIS:
                technical_findings.extend(result.findings)
                
        if not fundamental_findings or not technical_findings:
            telemetry.end_agent_run(run_id, status="skipped")
            return AgentResult(
                agent_role=self.role,
                success=True,
                findings=[],
                warnings=["Missing fundamental or technical findings for synthesis."]
            )
            
        warnings = []
        # Check for obvious lookahead bias mentioned in fundamental findings
        for finding in fundamental_findings:
            if "haven't happened yet" in finding.lower() or "future actuals" in finding.lower():
                warnings.append("Lookahead bias detected: Valuation relies on future data.")
                
        if warnings:
            telemetry.end_agent_run(run_id, status="failed")
            return AgentResult(
                agent_role=self.role,
                success=False,
                findings=[],
                warnings=warnings
            )
            
        prompt = (
            f"You are the Synthesis Agent.\n"
            f"Fundamental Findings: {json.dumps(fundamental_findings)}\n"
            f"Technical Findings: {json.dumps(technical_findings)}\n"
            f"Explicitly synthesize these signals. If there is a conflict (e.g., Fundamentally Undervalued but Technically Weak), flag it prominently.\n"
            f"Output the final combined perspective."
        )
        
        # LLM interaction
        # response = await self.llm_client.generate(prompt=prompt)
        findings = ["Conflict check complete. Signals synthesized successfully. (Placeholder for LLM output)"]
        
        telemetry.end_agent_run(run_id, status="success")
        return AgentResult(
            agent_role=self.role,
            success=True,
            findings=findings,
        )
