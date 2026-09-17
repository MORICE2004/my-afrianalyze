from packages.schemas.portfolio import SavedPortfolio

class PortfolioContextInjector:
    """
    Injects deterministic portfolio data into a strict text context for RAG or LLM usage.
    """
    
    @staticmethod
    def build_context(portfolio: SavedPortfolio) -> str:
        """
        Formats a SavedPortfolio's deterministic weightings, P&L, drift, and evidence records 
        into a strict text context.
        """
        context_lines = []
        context_lines.append(f"Portfolio Name: {portfolio.name}")
        context_lines.append(f"Total Value: {portfolio.total_value:,.2f}\n")
        
        context_lines.append("Positions:")
        for pos in portfolio.positions:
            context_lines.append(f"- Ticker: {pos.ticker}")
            context_lines.append(f"  Weighting: {pos.weighting:.2%}")
            context_lines.append(f"  Unrealized P&L: {pos.unrealized_pnl:,.2f}")
            context_lines.append(f"  Drift from Target: {pos.drift:.2%}")
            
            if pos.evidence:
                context_lines.append("  Evidence Records:")
                for ev in pos.evidence:
                    date_str = ev.retrieved_at.strftime("%Y-%m-%d")
                    context_lines.append(f"    * [{date_str}] Source: {ev.source_name} - {ev.metric_id} (Value: {ev.value})")
            context_lines.append("")
        
        return "\n".join(context_lines)
