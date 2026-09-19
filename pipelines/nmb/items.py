"""Canonical line items and how to recognise them in NMB's statements.

Each section has a heading pattern (used to find the region on the page) and
item label patterns (matched against the normalised row label). Units are
TZS millions unless stated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ItemSpec:
    code: str
    label: str
    pattern: str
    unit: str = "TZS_millions"
    # Which numeric cells to read. "last2" = (current, comparative) are the last two numbers.
    mode: str = "last2"
    first_only: bool = True


@dataclass(frozen=True)
class Section:
    code: str
    statement: str  # IS, BS, CF, NOTE
    heading: str
    basis: str
    items: list[ItemSpec] = field(default_factory=list)
    stop_headings: tuple[str, ...] = ()


IS_ITEMS = [
    ItemSpec("interest_income", "Interest income", r"^interest (and similar )?income$"),
    ItemSpec("interest_expense", "Interest expense", r"^interest (and similar )?expenses?$"),
    ItemSpec("net_interest_income", "Net interest income", r"^net interest income$"),
    ItemSpec("impairment_loans", "Impairment charge on loans and advances",
             r"^(impairment (charges?|losses) ?(-|on)? ?loans and advances.*|credit loss expense on loans.*|credit/\(charges?\) ?-? ?loans and advances.*)$"),
    ItemSpec("total_impairment", "Total impairment charge", r"^(total impairment (charges?|losses)|total credit loss expense|total credit/\(charges?\))$"),
    ItemSpec("fee_commission_income", "Fee and commission income", r"^fees? and commission income$"),
    ItemSpec("fee_commission_expense", "Fee and commission expense", r"^fees? and commission expenses?$"),
    ItemSpec("net_fee_commission_income", "Net fee and commission income", r"^net fees? and commission income$"),
    ItemSpec("fx_income", "Foreign exchange income", r"^(net )?foreign exchange (income|gains?)$"),
    ItemSpec("other_income", "Other income", r"^other (operating )?income$"),
    ItemSpec("total_operating_income", "Total operating income (after impairment)",
             r"^(total operating income|net operating income)$"),
    ItemSpec("employee_benefits", "Employee benefits expense", r"^(employee benefits? expenses?|staff costs)$"),
    ItemSpec("other_operating_expenses", "Other operating expenses", r"^other operating expenses$"),
    ItemSpec("depreciation_amortisation", "Depreciation and amortisation", r"^depreciation and amorti[sz]ation.*$"),
    ItemSpec("total_operating_expenses", "Total operating expenses", r"^total operating expenses$"),
    ItemSpec("profit_before_tax", "Profit before tax", r"^profit before (income )?tax(ation)?$"),
    ItemSpec("income_tax", "Income tax expense", r"^income tax (expense|charge)$"),
    ItemSpec("profit_for_year", "Profit for the year", r"^profit for the year$"),
    ItemSpec("profit_attributable_owners", "Profit attributable to owners of the bank",
             r"^(owners of the (bank|parent|company)|equity holders of the (bank|parent|company))$"),
    ItemSpec("eps", "Basic and diluted earnings per share", r"^basic (and diluted )?earnings per share.*$",
             unit="TZS_per_share"),
]

BS_ITEMS = [
    ItemSpec("cash_and_bot", "Cash and balances with Bank of Tanzania",
             r"^cash and balances with (the )?bank of tanzania$"),
    ItemSpec("placements_banks", "Placements and balances with other banks",
             r"^(placements and balances with other banks|loans and advances to banks|balances with other banks|placements with other banks)$"),
    ItemSpec("loans_advances_net", "Loans and advances to customers", r"^loans and advances to customers$"),
    ItemSpec("inv_securities_amortised_cost", "Investment securities at amortised cost",
             r"^(- ?)?(investment securities )?(at|measured at) amorti[sz]ed cost$"),
    ItemSpec("inv_securities_fvoci", "Investment securities at FVOCI",
             r"^(- ?)?(investment securities )?at (fvoci|fair value through other comprehensive income)$"),
    ItemSpec("inv_securities_fvpl", "Investment securities at FVPL",
             r"^(- ?)?(investment securities )?at (fvpl|fvtpl|fair value through profit or loss)$"),
    ItemSpec("total_assets", "Total assets", r"^total assets$"),
    ItemSpec("deposits_banks", "Deposits due to other banks", r"^deposits (due to|from) (other )?banks$"),
    ItemSpec("deposits_customers", "Deposits from customers", r"^deposits from customers$"),
    ItemSpec("borrowings", "Borrowings", r"^borrowings$"),
    ItemSpec("other_liabilities", "Other liabilities", r"^other liabilities$"),
    ItemSpec("total_liabilities", "Total liabilities", r"^total liabilities$"),
    ItemSpec("share_capital", "Share capital", r"^share capital$"),
    ItemSpec("retained_earnings", "Retained earnings", r"^retained earnings$"),
    ItemSpec("equity_owners", "Equity attributable to owners of the bank",
             r"^((capital and reserves|equity|total equity) attributable to (the )?(owners|equity holders|shareholders) of the (parent|bank|company)|capital and reserves attributable to owners of the parent)$"),
    ItemSpec("nci", "Non-controlling interest", r"^non-? ?controlling interests?$"),
    ItemSpec("total_equity", "Total equity", r"^total (equity|shareholders.? (equity|funds))$"),
    ItemSpec("total_equity_and_liabilities", "Total equity and liabilities",
             r"^total (equity and liabilities|liabilities and (shareholders.? )?equity)$"),
]

CF_ITEMS = [
    ItemSpec("net_cash_operating", "Net cash from operating activities",
             r"^net cash .*(operations|operating activities)$"),
    ItemSpec("net_cash_investing", "Net cash from investing activities", r"^net cash .*investing activities$"),
    ItemSpec("net_cash_financing", "Net cash from financing activities", r"^net cash .*financing( activities)?$"),
    ItemSpec("dividends_paid", "Dividends paid", r"^dividends? paid$"),
    ItemSpec("cash_end", "Cash and cash equivalents at end of year",
             r"^cash and cash equivalents at (the )?end of (the )?(year|period)$"),
]

CAPITAL_ITEMS = [
    ItemSpec("cet1_capital", "Common equity tier 1 capital",
             r"^(available common equity tier( 1)?.*|total qualifying tier 1 capital.*|total tier 1 capital|core capital.*)$"),
    ItemSpec("total_regulatory_capital", "Total regulatory capital", r"^total (regulatory )?capital( \(d\).*)?$"),
    ItemSpec("total_rwa", "Total risk-weighted assets",
             r"^total risk[- ]?weighted assets.*$"),
]

LOANS_NOTE_ITEMS = [
    ItemSpec("gross_loans", "Gross loans and advances to customers",
             r"^gross loans and advances to customers.*$"),
    ItemSpec("ecl_loans", "Expected credit losses on loans",
             r"^less:? ?(allowance for )?(expected credit loss(es)?|impairment).*$"),
]

STAGE_ITEMS = [
    # Row "As at 31 December <year>" has stage 1, stage 2, stage 3, total.
    ItemSpec("stage3_gross_loans", "Stage 3 (credit-impaired) gross loans",
             r"^(as at|balance at) 31 december {year}$", mode="stage3_of_4"),
]

SECTIONS = [
    Section("IS", "IS", r"^consolidated statement of profit or loss", "consolidated", IS_ITEMS),
    Section("BS", "BS", r"^consolidated statement of financial position", "consolidated", BS_ITEMS),
    Section("CF", "CF", r"^consolidated statement of cash flows?", "consolidated", CF_ITEMS),
]

NOTE_SECTIONS = [
    Section("CAPITAL", "NOTE", r"^\d+(\.\d+)*\.? ?capital management", "bank", CAPITAL_ITEMS),
    Section("LOANS", "NOTE", r"^\d{1,2}\.? ?(\(a\) )?loans and advances to customers", "consolidated", LOANS_NOTE_ITEMS),
    Section("STAGES", "NOTE", r"^(\d+(\.\d+)*\.? ?)?changes in (the )?gross carrying amount", "bank", STAGE_ITEMS),
]

ALL_ITEMS = {i.code: (s, i) for s in SECTIONS + NOTE_SECTIONS for i in s.items}


def normalise_label(text: str) -> str:
    t = text.replace("’", "'").replace("‘", "'").replace("�", "'")
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
