"""One profile per bank: where its reports are, how it words and lays out its
statements, which tie checks apply, and which risks it states.

Adding a bank means adding a profile here, running the pipeline, and checking the
results against the PDFs by hand (tests/v1/test_<bank>_integration.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pipelines.banks.items import ItemSpec, Section, item, with_patterns

# ---------------------------------------------------------------- shared items (NMB wording)

IS_ITEMS = [
    item("interest_income", r"^interest (and similar )?income$"),
    item("interest_expense", r"^interest (and similar )?expenses?$"),
    item("net_interest_income", r"^net interest income$"),
    item("impairment_loans",
         r"^(impairment (charges?|losses) ?(-|on)? ?loans and advances.*|credit loss expense on loans.*|credit/\(charges?\) ?-? ?loans and advances.*)$"),
    item("total_impairment", r"^(total impairment (charges?|losses)|total credit loss expense|total credit/\(charges?\))$"),
    item("fee_commission_income", r"^fees? and commission income$"),
    item("fee_commission_expense", r"^fees? and commission expenses?$"),
    item("net_fee_commission_income", r"^net fees? and commission income$"),
    item("fx_income", r"^(net )?foreign exchange (income|gains?)$"),
    item("other_income", r"^other (operating )?income$"),
    item("total_operating_income", r"^(total operating income|net operating income)$"),
    item("employee_benefits", r"^(employee benefits? expenses?|staff costs)$"),
    item("other_operating_expenses", r"^other operating expenses$"),
    item("depreciation_amortisation", r"^depreciation and amorti[sz]ation.*$"),
    item("total_operating_expenses", r"^total operating expenses$"),
    item("profit_before_tax", r"^profit before (income )?tax(ation)?$"),
    item("income_tax", r"^income tax (expense|charge)$"),
    item("profit_for_year", r"^profit for the year$"),
    item("profit_attributable_owners",
         r"^(owners of the (bank|parent|company)|equity holders of the (bank|parent|company))$"),
    item("eps", r"^basic (and diluted )?earnings per share.*$"),
]

BS_ITEMS = [
    item("cash_and_bot", r"^cash and balances with (the )?bank of tanzania$"),
    item("placements_banks",
         r"^(placements and balances with other banks|loans and advances to banks|balances with other banks|placements with other banks)$"),
    item("loans_advances_net", r"^loans and advances to customers$"),
    item("inv_securities_amortised_cost", r"^(- ?)?(investment securities )?(at|measured at) amorti[sz]ed cost$"),
    item("inv_securities_fvoci", r"^(- ?)?(investment securities )?at (fvoci|fair value through other comprehensive income)$"),
    item("inv_securities_fvpl", r"^(- ?)?(investment securities )?at (fvpl|fvtpl|fair value through profit or loss)$"),
    item("total_assets", r"^total assets$"),
    item("deposits_banks", r"^deposits (due to|from) (other )?banks$"),
    item("deposits_customers", r"^deposits from customers$"),
    item("borrowings", r"^borrowings$"),
    item("other_liabilities", r"^other liabilities$"),
    item("total_liabilities", r"^total liabilities$"),
    item("share_capital", r"^share capital$"),
    item("retained_earnings", r"^retained earnings$"),
    item("equity_owners",
         r"^((capital and reserves|equity|total equity) attributable to (the )?(owners|equity holders|shareholders) of the (parent|bank|company)|capital and reserves attributable to owners of the parent)$"),
    item("nci", r"^non-? ?controlling interests?$"),
    item("total_equity", r"^total (equity|shareholders.? (equity|funds))$"),
    item("total_equity_and_liabilities", r"^total (equity and liabilities|liabilities and (shareholders.? )?equity)$"),
]

CF_ITEMS = [
    item("net_cash_operating", r"^net cash .*(operations|operating activities)$"),
    item("net_cash_investing", r"^net cash .*investing activities$"),
    item("net_cash_financing", r"^net cash .*financing( activities)?$"),
    item("dividends_paid", r"^dividends? paid$"),
    item("cash_end", r"^cash and cash equivalents at (the )?end of (the )?(year|period)$"),
]

CAPITAL_ITEMS = [
    item("cet1_capital",
         r"^(available common equity tier( 1)?.*|total qualifying tier 1 capital.*|total tier 1 capital|core capital.*)$"),
    item("total_regulatory_capital", r"^total (regulatory )?capital( \(d\).*)?$"),
    item("total_rwa", r"^total risk[- ]?weighted assets.*$"),
]

LOANS_NOTE_ITEMS = [
    item("gross_loans", r"^gross loans and advances to customers.*$"),
    item("ecl_loans", r"^less:? ?(allowance for )?(expected credit loss(es)?|impairment).*$"),
]

# Standard tie checks: (name, left item, right items, critical)
STANDARD_TIES = [
    ("assets = liabilities + equity", "total_assets", ["total_liabilities", "total_equity"], True),
    ("total equity and liabilities = total assets", "total_equity_and_liabilities", ["total_assets"], True),
    ("total equity = owners + non-controlling", "total_equity", ["equity_owners", "nci"], False),
    ("net interest income = interest income + interest expense", "net_interest_income",
     ["interest_income", "interest_expense"], False),
    ("profit before tax = operating income + operating expenses", "profit_before_tax",
     ["total_operating_income", "total_operating_expenses"], False),
    ("profit for the year = profit before tax + income tax", "profit_for_year",
     ["profit_before_tax", "income_tax"], False),
    ("net loans = gross loans + ECL allowance", "loans_advances_net", ["gross_loans", "ecl_loans"], False),
]

APPROVAL_RE = (r"authori[sz]ed for issue by the Board of Directors.{0,200}?"
               r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June)\s+(\d{4})")
DPS_RE = (r"dividend of TZS\s*([\d,]+(?:\.\d+)?)\s*per\s+share[^.]{0,160}?(?:out of|for)\s+(?:the\s+)?"
          r"(?:year\s+)?(\d{4})")


@dataclass(frozen=True)
class BankProfile:
    key: str                      # "nmb"
    security_id: str              # "DSE:NMB"
    name: str                     # "NMB Bank Plc"
    listing_url: str              # investor relations page the reports are listed on
    reports: dict[int, str]       # fiscal year -> download URL
    sections: list[Section]
    note_sections: list[Section]
    columns: str = "last2"        # "last2": current, comparative are the last two numbers
                                  # "group_first": GROUP cur, GROUP prior, BANK cur, BANK prior
    ties: list[tuple] = field(default_factory=lambda: list(STANDARD_TIES))
    dps_page_hint: str = r"dividend per share"
    dps_re: str = DPS_RE
    approval_re: str = APPROVAL_RE
    wrap_label_max: int = 40      # a label wrapped onto the next row is joined when that row's label is shorter
    label_noise: tuple[str, ...] = ()        # running-header text glued to the start of row labels
    label_fixes: tuple[tuple[str, str], ...] = ()  # wrong glyphs in a report's text layer -> letters
    # (target item, source item or None for nil, regex that must appear in the report that supplied the
    #  source figure). Used only when the target is not printed for that year.
    derivations: tuple[tuple[str, str | None, str], ...] = ()
    risks: list[tuple] = field(default_factory=list)
    terms_note: str = ""

    @property
    def raw_dir(self) -> Path:
        return Path("data/raw") / self.key

    @property
    def processed_dir(self) -> Path:
        return Path("data/processed") / self.key

    def pdf_path(self, year: int) -> Path:
        return self.raw_dir / f"{self.key.upper()}_Annual_Report_{year}.pdf"

    @property
    def years(self) -> list[int]:
        return sorted(self.reports)

    @property
    def all_sections(self) -> list[Section]:
        return self.sections + self.note_sections

    @property
    def all_items(self) -> dict[str, tuple[Section, ItemSpec]]:
        return {i.code: (s, i) for s in self.all_sections for i in s.items}


# ---------------------------------------------------------------- NMB Bank Plc

_NMB_IR = "https://www.nmbbank.co.tz/investor-relations-nmb/financial-and-regulatory-reports/annual-reports"

NMB = BankProfile(
    key="nmb",
    security_id="DSE:NMB",
    name="NMB Bank Plc",
    listing_url=_NMB_IR,
    reports={
        2025: f"{_NMB_IR}?download=479:nmb-integrated-annual-report-2025",
        2024: f"{_NMB_IR}?download=426:nmb-integrated-annual-report-2024",
        2023: f"{_NMB_IR}?download=394:nmb-integrated-annual-report-2023",
        2022: f"{_NMB_IR}?download=361:annual-report-2022",
        2021: f"{_NMB_IR}?download=339:annual-report-2021",
    },
    sections=[
        Section("IS", "IS", r"^consolidated statement of profit or loss", "consolidated", IS_ITEMS),
        Section("BS", "BS", r"^consolidated statement of financial position", "consolidated", BS_ITEMS),
        Section("CF", "CF", r"^consolidated statement of cash flows?", "consolidated", CF_ITEMS),
    ],
    note_sections=[
        Section("CAPITAL", "NOTE", r"^\d+(\.\d+)*\.? ?capital management", "bank", CAPITAL_ITEMS),
        Section("LOANS", "NOTE", r"^\d{1,2}\.? ?(\(a\) )?loans and advances to customers", "consolidated",
                LOANS_NOTE_ITEMS),
        Section("STAGES", "NOTE", r"^(\d+(\.\d+)*\.? ?)?changes in (the )?gross carrying amount", "bank",
                [item("stage3_gross_loans", r"^(as at|balance at) 31 december {year}$", mode="stage3_of_4")]),
    ],
    terms_note=("Published by NMB Bank Plc on its public investor relations page. Terms of use for reuse in a "
                "research product have not been reviewed yet (PRODUCT_CONTEXT.md section 73)."),
    # (category, title, report year, page, regex that must match the page text)
    risks=[
        ("macro_currency", "Macroeconomic and currency conditions", 2025, 107,
         r"While the economy remains resilient.*?net interest margins\."),
        ("macro_currency", "Indirect geopolitical and foreign-exchange effects", 2025, 107,
         r"The geopolitical developments at the regional and global level.*?investor confidence\."),
        ("regulatory", "Evolving regulatory and legal environment", 2025, 107,
         r"The Tanzanian regulatory and legal environment continues to evolve[^.]*?(?:\.|$)"),
        ("regulatory", "Bank of Tanzania capital requirements", 2025, 197,
         r"Maintain total capital of not less than 12% of risk-weighted assets.*?items\."),
        ("credit_concentration", "Concentration limits in the risk appetite", 2025, 73,
         r"The Bank.s risk appetite statement is approved by the Board.*?business mix\."),
        ("credit_concentration", "Credit growth balanced against concentration", 2025, 86,
         r"NMB Bank continued to emphasize risk-adjusted returns.*?earnings\."),
        ("governance_ownership", "Concentrated ownership: two strategic shareholders", 2025, 113,
         r"Arise B\.?V\.?.{0,40}?174,500,000.{0,40}?34\.90\s*%"),
        ("governance_ownership", "Government shareholding via the Treasury Registrar", 2025, 113,
         r"The Treasury Registrar \(Government of Tanzania\).{0,20}?158,901,800.{0,20}?31\.78\s*%"),
        ("esg", "Environmental and social risk in lending", 2025, 47,
         r"NMB Bank PLC.s Environmental and Social Management Policy \(ESMP\) framework governs.*?investment activities\."),
    ],
)

# ---------------------------------------------------------------- CRDB Bank Plc
# Statements show four columns: GROUP current, GROUP prior, BANK current, BANK prior. The consolidated
# (GROUP) columns are used, as for NMB. Interest income and expense are each split over two lines, and the
# loan impairment charge comes from the credit loss expense note (a stage table).

_CRDB_IR = "https://crdbbank.co.tz/en/investor-relations/reports?type=annual_reports"
_CRDB_MEDIA = "https://crdbbank.co.tz/storage/app/media"
# "STATEMENT OR PROFIT OR LOSS" is a typo in the 2023 report; a following number means an OCI line, not a heading.
_ANY_STATEMENT = r"^(consolidated (and separate )?)?statements? o[fr] "

CRDB = BankProfile(
    key="crdb",
    security_id="DSE:CRDB",
    name="CRDB Bank Plc",
    listing_url=_CRDB_IR,
    reports={
        2025: f"{_CRDB_MEDIA}/Our%20Investors/Annual%20Reports/crdb-ir-2025-8th-may-2026.pdf",
        2024: f"{_CRDB_MEDIA}/Our%20Investors/Annual%20Reports/2024%20Integrated%20Annual%20Report%20and%20"
              "Consolidated%20Audited%20Financial%20Statements%20.pdf",
        2023: f"{_CRDB_MEDIA}/2023%20CRDB%20BANK%20ANNUAL%20REPORT.pdf",
        2022: f"{_CRDB_MEDIA}/2022%20CRDB%20Annual%20Report-final_.pdf",
        2021: f"{_CRDB_MEDIA}/Our%20Investors/Annual%20Reports/CRDB-Group-and-Bank-Annual-Report-2021.pdf",
    },
    columns="group_first",
    wrap_label_max=60,
    sections=[
        Section("IS", "IS", _ANY_STATEMENT + r"profit or loss(?! *[\d(])", "consolidated", [
            item("interest_income_eir", r"^interest income calculated using the( effective( interest method)?)?$"),
            item("interest_income_other", r"^other interest and similar income$"),
            item("interest_expense_eir", r"^interest expense calculated using the( effective( interest method)?)?$"),
            item("interest_expense_other", r"^other interest and similar expenses?$"),
        ] + with_patterns(IS_ITEMS, {
            "interest_income": None,
            "interest_expense": None,
            "impairment_loans": None,  # from the credit loss expense note
            "total_impairment": r"^credit loss expense on financial assets$",
            "employee_benefits": r"^employees? benefits? expenses?$",
            "other_operating_expenses": r"^(operating expenses|general and administrative expenses)$",
            "profit_attributable_owners": r"^(equity holders of the parent|owners of the parent( entity)?)$",
            "depreciation_amortisation": None,  # reported as two separate lines
            "eps": None,
        }) + [item("eps", r"^basic (and diluted )?earnings per share.*$", mode="columns_min2")]),
        Section("BS", "BS", _ANY_STATEMENT + "financial position", "consolidated",
                with_patterns(BS_ITEMS, {
                    "cash_and_bot": r"^cash and balances with (the )?central bank$",
                    "placements_banks": r"^due from banks$",
                    "inv_securities_amortised_cost": r"^debt instruments? at amorti[sz]ed cost$",
                    "inv_securities_fvoci": r"^debt instruments? at (fvoci|fair value through( other com.*)?)$",
                    "inv_securities_fvpl": r"^financial assets at (fvpl|fair value through( profit or( loss)?)?)$",
                    "deposits_banks": r"^(deposits and )?balances due to other banks$",
                    "deposits_customers": r"^deposits from customers?$",
                    "equity_owners": r"^total equity attributable to (the )?(parent|equity holders of the parent)$",
                    "nci": r"^total equity attributable to non-?( ?controlling.*)?$",
                })),
        Section("CF", "CF", _ANY_STATEMENT + r"cash ?flows?", "consolidated",
                with_patterns(CF_ITEMS, {
                    "net_cash_operating": r"^net cash .*(operations|operating activ.*|used in)$",
                    "net_cash_financing": r"^net cash .*financ.*$",
                    "cash_end": r"^cash and cash equivalents at (the )?(end of (the )?(year|period)|31 december)$",
                })),
    ],
    note_sections=[
        Section("CAPITAL", "NOTE", r"^\d+(\.\d+)*\.? ?capital management", "consolidated", CAPITAL_ITEMS),
        Section("LOANS", "NOTE", r"^\d{1,2}\.? ?(\(a\) )?loans and advances to customers", "consolidated", [
            # 2025 and 2022 also print a GROUP/BANK row; 2021-2024 only print stage tables, whose first
            # two tables are GROUP current and GROUP prior. The net-loans tie check guards both readings.
            item("gross_loans", r"^gross loans and advances to customers.*$"),
            item("gross_loans", r"^gross loans and advances to customers$", mode="total_by_order"),
            item("ecl_loans", r"^(.{2,5}: ?)?(provision|allowance) for impairment.*$"),
            item("ecl_loans", r"^(.{2,5}: ?)?(provision|allowance) for impairment$", mode="total_by_order"),
            item("stage3_gross_loans", r"^gross loans and advances to customers$", mode="stage3_by_total"),
        ]),
        Section("CREDITLOSS", "NOTE", r"^\d{1,2}\.? ?credit loss expense", "consolidated", [
            item("impairment_loans", r"^loans and advances to customers$", mode="total_by_order"),
        ]),
    ],
    ties=[t for t in STANDARD_TIES if not t[0].startswith("net interest income")] + [
        ("net interest income = interest income + interest expense (both lines each)", "net_interest_income",
         ["interest_income_eir", "interest_income_other", "interest_expense_eir", "interest_expense_other"], False),
    ],
    dps_page_hint=r"dividend",
    approval_re=(r"authori[sz]ed for issue by (?:the Board of Directors|those charged with governance).{0,200}?"
                 r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June)\s+(\d{4})"),
    label_noise=(r"^group and bank annual report 20\d\d\s*", r"^sustainable value for growth\s*",
                 r"^financial statements for the year ended 31 december 20\d\d\s*"),
    # The 2022 and 2023 PDFs map some letters to the wrong glyphs ("proﬁt beǌore inƥoǽe taɫ").
    # Word-level, applied after Unicode normalisation (which turns "ǌ" into "nj").
    label_fixes=(("benjore", "before"), ("njor ", "for "), ("inƥoǽe", "income"), ("taɫ", "tax"),
                 ("jeȷȷ:", "less:")),
    derivations=(
        # 2021 and 2022 reports print no owners/NCI split and state that all subsidiaries are wholly owned.
        ("equity_owners", "total_equity", r"subsidiaries are 100% owned by the parent entity"),
        ("nci", None, r"subsidiaries are 100% owned by the parent entity"),
    ),
    terms_note=("Published by CRDB Bank Plc on its public investor relations page. Terms of use for reuse in a "
                "research product have not been reviewed yet (PRODUCT_CONTEXT.md section 73)."),
    risks=[
        ("macro_currency", "Market and foreign exchange risk", 2025, 20,
         r"Adverse movements in interest rates, exchange rates and security prices can affect earnings, "
         r"valuation and customer affordability\."),
        ("macro_currency", "Funding costs from deposit competition", 2025, 20,
         r"Competition for deposits and alternative yields in government securities increased funding costs\."),
        ("regulatory", "Compliance and regulatory risk", 2025, 20,
         r"Regulatory breaches or misinterpretation can lead to fines, remediation costs and reputational damage\."),
        ("regulatory", "Tighter oversight of channel fees", 2025, 20,
         r"Tighter oversight of channel fees constrained some non.?funded income lines\."),
        ("regulatory", "Bank of Tanzania capital requirements", 2025, 101,
         r"These figures significantly exceed the minimum regulatory requirements of 12\.5% for Tier I capital "
         r"and 14\.5% for Tier II capital.*?stability\."),
        ("credit_concentration", "Credit risk", 2025, 20,
         r"Deterioration in borrower cash flows, sector stress, or collateral weakness can impair earnings and "
         r"capital through higher ECL and NPLs\."),
        ("credit_concentration", "Deposit concentration and liquidity", 2025, 20,
         r"Deposit concentration shifts, maturity mismatch or funding-market stress can affect the ability to "
         r"meet obligations and fund growth\."),
        ("governance_ownership", "Government influence through DANIDA Investment Fund and pension funds", 2025, 332,
         r"The Government of Tanzania owns 34\.3% \(2024: 34\.3%\) equity in the Bank through DANIDA Investment "
         r"funds and Pension Funds and has significant influence\."),
        ("esg", "Climate-related risk", 2025, 20,
         r"Physical and transition risks can affect customers, collateral values, operating sites and future "
         r"access to capital\."),
    ],
)

PROFILES: dict[str, BankProfile] = {"nmb": NMB, "crdb": CRDB}


def profile_for(key_or_security: str) -> BankProfile | None:
    k = key_or_security.lower()
    for p in PROFILES.values():
        if k in (p.key, p.security_id.lower()):
            return p
    return None
