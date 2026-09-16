from typing import List, Dict, Any

def residual_income_valuation(book_value: float, roe: float, cost_of_equity: float, growth_rate: float, forecast_years: int = 5) -> Dict[str, Any]:
    """Gordon Growth variant of residual income: P = BV + (ROE - CoE) * BV / (CoE - g)
    Commonly used for banks where cash flows are hard to define."""
    warnings = []
    if cost_of_equity <= growth_rate:
        warnings.append("Cost of equity must be greater than growth rate for Gordon Growth formula.")
        fair_value = 0.0
    else:
        residual_income_terminal = (roe - cost_of_equity) * book_value / (cost_of_equity - growth_rate)
        fair_value = book_value + residual_income_terminal

    return {
        "fair_value": fair_value,
        "methodology": "Residual Income Valuation (Gordon Growth variant)",
        "assumptions_used": {
            "book_value": book_value,
            "roe": roe,
            "cost_of_equity": cost_of_equity,
            "growth_rate": growth_rate,
            "forecast_years": forecast_years
        },
        "warnings": warnings
    }

def dividend_discount_model(current_dps: float, growth_rates: List[float], terminal_growth: float, cost_of_equity: float) -> Dict[str, Any]:
    """Multi-stage DDM. Banks are natural dividend payers, making DDM appropriate."""
    warnings = []
    fair_value = 0.0
    dps = current_dps
    
    if cost_of_equity <= terminal_growth:
        warnings.append("Cost of equity must be greater than terminal growth rate.")
        return {
            "fair_value": 0.0,
            "methodology": "Dividend Discount Model (Multi-stage)",
            "assumptions_used": {"current_dps": current_dps, "growth_rates": growth_rates, "terminal_growth": terminal_growth, "cost_of_equity": cost_of_equity},
            "warnings": warnings
        }

    for i, g in enumerate(growth_rates):
        dps *= (1 + g)
        fair_value += dps / ((1 + cost_of_equity) ** (i + 1))
    
    terminal_value = (dps * (1 + terminal_growth)) / (cost_of_equity - terminal_growth)
    fair_value += terminal_value / ((1 + cost_of_equity) ** len(growth_rates))

    return {
        "fair_value": fair_value,
        "methodology": "Dividend Discount Model (Multi-stage)",
        "assumptions_used": {
            "current_dps": current_dps,
            "growth_rates": growth_rates,
            "terminal_growth": terminal_growth,
            "cost_of_equity": cost_of_equity
        },
        "warnings": warnings
    }

def pb_relative_valuation(target_roe: float, cost_of_equity: float, growth_rate: float) -> float:
    """Justified P/B = (ROE - g) / (CoE - g). Theoretically grounded P/B."""
    if cost_of_equity <= growth_rate:
        return 0.0
    return (target_roe - growth_rate) / (cost_of_equity - growth_rate)

def pe_relative_valuation(target_roe: float, payout_ratio: float, cost_of_equity: float, growth_rate: float) -> float:
    """Justified P/E from Gordon Growth: P/E = payout / (CoE - g)"""
    if cost_of_equity <= growth_rate:
        return 0.0
    return payout_ratio / (cost_of_equity - growth_rate)
