"""Rule-based "what moved and why it matters" notes for statement lines.

Every number in a note is computed here from sourced facts. A language model may
rephrase a note for readability but must keep these numbers unchanged; the
`numbers` field lists them so a rephrasing can be checked.
"""
from __future__ import annotations

from packages.analysis.bank_ratios import Facts, get


def _growth(facts: Facts, item: str, year: int):
    cur, prev = get(facts, item, year), get(facts, item, year - 1)
    if cur is None or prev is None or prev == 0:
        return None
    # Growth in size. Expense lines are stored as negative numbers, so compare magnitudes.
    return (abs(cur) - abs(prev)) / abs(prev)


def _pct(x) -> str:
    return f"{x * 100:+.1f}%"


def _bn(x) -> str:
    return f"TZS {x / 1000:,.1f} bn"


# item -> (related item, its label, meaning when item grows faster, meaning when it grows more slowly).
# The meanings are about relative growth, so they stay true when either line shrinks.
PAIRS = {
    "impairment_loans": ("gross_loans", "gross loans",
                         "credit costs are higher relative to the loan book, which raises cost of risk",
                         "credit costs are lower relative to the loan book, which lowers cost of risk"),
    "total_operating_expenses": ("operating_income_pre_impairment", "operating income before impairment",
                                 "costs outgrowing income (negative jaws), which pushes cost-to-income up",
                                 "income outgrowing costs (positive jaws), which improves cost-to-income"),
    "loans_advances_net": ("deposits_customers", "customer deposits",
                           "lending outpacing deposit funding, which raises the loan-to-deposit ratio",
                           "deposit funding outpacing lending, which lowers the loan-to-deposit ratio"),
    "net_interest_income": ("interest_income", "interest income",
                            "funding costs growing more slowly than interest earned, supporting the margin",
                            "funding costs growing faster than interest earned, squeezing the margin"),
    "profit_attributable_owners": ("equity_owners", "shareholders' equity",
                                   "earnings growing faster than the equity base, lifting ROE",
                                   "the equity base growing faster than earnings, diluting ROE"),
    "deposits_customers": ("total_assets", "total assets",
                           "deposits funding a growing share of the balance sheet",
                           "a shrinking share of the balance sheet funded by deposits"),
}


def _compare(label: str, g, other_label: str, og) -> str:
    """Describe relative growth without contradicting the direction of either line."""
    if g == og:
        return f"{label} moved in line with {other_label}"
    if g >= 0 and og >= 0:
        return f"{label} grew {'faster' if g > og else 'more slowly'} than {other_label}"
    if g < 0 <= og:
        return f"{label} fell while {other_label} grew"
    if og < 0 <= g:
        return f"{label} grew while {other_label} fell"
    return f"{label} fell {'less' if g > og else 'more'} than {other_label}"


def line_note(facts: Facts, item: str, label: str, year: int) -> dict | None:
    cur = get(facts, item, year)
    g = _growth(facts, item, year)
    if cur is None or g is None:
        return None
    size_word = "rose" if g >= 0 else "fell"
    text = f"{label} {size_word} {abs(g) * 100:.1f}% to {_bn(abs(cur))} in {year}."
    numbers = [round(abs(g) * 100, 1), round(abs(cur) / 1000, 1), year]
    pair = PAIRS.get(item)
    if pair:
        other, other_label, faster_msg, slower_msg = pair
        og = _growth(facts, other, year)
        if og is not None and g != og:
            text += (f" Over the same year {other_label} changed {_pct(og)}, so "
                     f"{_compare(label.lower(), g, other_label, og)}: {faster_msg if g > og else slower_msg}.")
            numbers.append(round(og * 100, 1))
    return {"text": text, "numbers": numbers, "rule": f"growth of {item}" + (f" vs {pair[0]}" if pair else "")}
