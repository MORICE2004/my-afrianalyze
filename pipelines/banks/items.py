"""Canonical bank line items and the building blocks for recognising them.

Codes, labels and units are shared by every bank, so ratios, valuation and the
report work the same way for all of them. How each bank prints a line (its
label wording and column layout) lives in its profile (pipelines/banks/profiles.py).
Units are TZS millions unless stated.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ItemSpec:
    code: str
    label: str
    pattern: str
    unit: str = "TZS_millions"
    # How to read the numbers of a matched row:
    #   "columns"         (current, comparative) from the bank's column layout (profile.columns)
    #   "stage3_of_4"     row "As at 31 December <year>" = stage 1, 2, 3, total; takes stage 3 (NMB)
    #   "stage3_by_total" row = stage 1, 2, 3, total (1 + 2 + 3 = total); takes stage 3, and the
    #                     resolver keeps the row whose total equals gross loans for that year (CRDB)
    #   "columns_min2"    like "columns", but a row with only two numbers is read as (current, prior);
    #                     for lines a GROUP/BANK report prints for the GROUP only (CRDB EPS 2021-2022)
    #   "total_by_order"  row = stage 1, 2, 3, total; takes the total. The first such row in the
    #                     section is the current year, the second the prior year (CRDB credit loss note)
    mode: str = "columns"
    first_only: bool = True


@dataclass(frozen=True)
class Section:
    code: str
    statement: str  # IS, BS, CF, NOTE
    heading: str
    basis: str
    items: list[ItemSpec] = field(default_factory=list)
    stop_headings: tuple[str, ...] = ()


# code -> (label, unit). The order here is the order rows appear in the report.
CANONICAL: dict[str, tuple[str, str]] = {
    # income statement
    "interest_income": ("Interest income", "TZS_millions"),
    "interest_income_eir": ("Interest income (effective interest method)", "TZS_millions"),
    "interest_income_other": ("Other interest and similar income", "TZS_millions"),
    "interest_expense": ("Interest expense", "TZS_millions"),
    "interest_expense_eir": ("Interest expense (effective interest method)", "TZS_millions"),
    "interest_expense_other": ("Other interest and similar expenses", "TZS_millions"),
    "net_interest_income": ("Net interest income", "TZS_millions"),
    "impairment_loans": ("Impairment charge on loans and advances", "TZS_millions"),
    "total_impairment": ("Total impairment charge", "TZS_millions"),
    "fee_commission_income": ("Fee and commission income", "TZS_millions"),
    "fee_commission_expense": ("Fee and commission expense", "TZS_millions"),
    "net_fee_commission_income": ("Net fee and commission income", "TZS_millions"),
    "fx_income": ("Foreign exchange income", "TZS_millions"),
    "other_income": ("Other income", "TZS_millions"),
    "total_operating_income": ("Total operating income (after impairment)", "TZS_millions"),
    "employee_benefits": ("Employee benefits expense", "TZS_millions"),
    "other_operating_expenses": ("Other operating expenses", "TZS_millions"),
    "depreciation_amortisation": ("Depreciation and amortisation", "TZS_millions"),
    "total_operating_expenses": ("Total operating expenses", "TZS_millions"),
    "profit_before_tax": ("Profit before tax", "TZS_millions"),
    "income_tax": ("Income tax expense", "TZS_millions"),
    "profit_for_year": ("Profit for the year", "TZS_millions"),
    "profit_attributable_owners": ("Profit attributable to owners of the bank", "TZS_millions"),
    "eps": ("Basic and diluted earnings per share", "TZS_per_share"),
    # balance sheet
    "cash_and_bot": ("Cash and balances with Bank of Tanzania", "TZS_millions"),
    "placements_banks": ("Placements and balances with other banks", "TZS_millions"),
    "loans_advances_net": ("Loans and advances to customers", "TZS_millions"),
    "inv_securities_amortised_cost": ("Investment securities at amortised cost", "TZS_millions"),
    "inv_securities_fvoci": ("Investment securities at FVOCI", "TZS_millions"),
    "inv_securities_fvpl": ("Investment securities at FVPL", "TZS_millions"),
    "total_assets": ("Total assets", "TZS_millions"),
    "deposits_banks": ("Deposits due to other banks", "TZS_millions"),
    "deposits_customers": ("Deposits from customers", "TZS_millions"),
    "borrowings": ("Borrowings", "TZS_millions"),
    "other_liabilities": ("Other liabilities", "TZS_millions"),
    "total_liabilities": ("Total liabilities", "TZS_millions"),
    "share_capital": ("Share capital", "TZS_millions"),
    "retained_earnings": ("Retained earnings", "TZS_millions"),
    "equity_owners": ("Equity attributable to owners of the bank", "TZS_millions"),
    "nci": ("Non-controlling interest", "TZS_millions"),
    "total_equity": ("Total equity", "TZS_millions"),
    "total_equity_and_liabilities": ("Total equity and liabilities", "TZS_millions"),
    # cash flow
    "net_cash_operating": ("Net cash from operating activities", "TZS_millions"),
    "net_cash_investing": ("Net cash from investing activities", "TZS_millions"),
    "net_cash_financing": ("Net cash from financing activities", "TZS_millions"),
    "dividends_paid": ("Dividends paid", "TZS_millions"),
    "cash_end": ("Cash and cash equivalents at end of year", "TZS_millions"),
    # notes
    "cet1_capital": ("Common equity tier 1 capital", "TZS_millions"),
    "total_regulatory_capital": ("Total regulatory capital", "TZS_millions"),
    "total_rwa": ("Total risk-weighted assets", "TZS_millions"),
    "gross_loans": ("Gross loans and advances to customers", "TZS_millions"),
    "ecl_loans": ("Expected credit losses on loans", "TZS_millions"),
    "stage3_gross_loans": ("Stage 3 (credit-impaired) gross loans", "TZS_millions"),
}


def item(code: str, pattern: str, mode: str = "columns") -> ItemSpec:
    label, unit = CANONICAL[code]
    return ItemSpec(code, label, pattern, unit=unit, mode=mode)


def with_patterns(items: list[ItemSpec], overrides: dict[str, str | None]) -> list[ItemSpec]:
    """Copy a list of items, replacing label patterns. A value of None drops the item
    (the bank does not report that line)."""
    out = []
    for i in items:
        if i.code in overrides:
            if overrides[i.code] is None:
                continue
            i = replace(i, pattern=overrides[i.code])
        out.append(i)
    return out


def normalise_label(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)  # ligatures such as "ﬁ" become "fi"
    t = t.replace("’", "'").replace("‘", "'").replace("�", "'")
    t = t.replace("–", "-").replace("—", "-")
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"\s*\(?note\s*\d+.*$", "", t)
    t = t.rstrip(" :")
    return t


NUMBER_RE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$")


def parse_number(cell: str) -> Decimal | None:
    """'1,780,949' -> 1780949; '(357,249)' -> -357249; '-' -> 0 (reported nil). Exact Decimal."""
    c = cell.strip().replace(" ", "")
    if c in {"-", "–", "—"}:
        return Decimal(0)
    if not NUMBER_RE.match(c):
        return None
    neg = c.startswith("(") and c.endswith(")")
    c = c.strip("()").replace(",", "")
    try:
        v = Decimal(c)
    except InvalidOperation:
        return None
    return -v if neg else v
