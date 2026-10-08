"""Rule-based tagging of news headlines: categories, countries, market relevance and links to AfriEdge data.

No model, no sentiment. Each rule names the economic variable it detects, and the relevance label is built from
three things the rules can show: which asset class is affected, which country, and which variable was disclosed.
A story that matches no rule is NOT_ASSESSED, never guessed. Swahili patterns are included because the Bank of
Tanzania publishes its press-release titles in Swahili.

Companies are linked only two ways: (1) the company's own name or ticker is in the headline, so the story is
about it; (2) a sector rule, e.g. a central-bank rate decision in Kenya is linked to the banks AfriEdge lists in
Kenya, labelled as a sector link. A company named only in passing in an article body is never linked, because
bodies are never read.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

COUNTRY_NAMES = {"TZ": "Tanzania", "KE": "Kenya", "UG": "Uganda"}
CURRENCY = {"TZ": "TZS", "KE": "KES", "UG": "UGX"}
EXCHANGE = {"TZ": "DSE", "KE": "NSE", "UG": "USE"}
WB_ISO3 = {"TZ": "TZA", "KE": "KEN", "UG": "UGA"}

# Ordered: the first matching rule that carries a relevance level sets it. Each entry: category, relevance,
# variable (plain words), asset classes, regex.
RULES: list[tuple[str, str | None, str, tuple[str, ...], str]] = [
    ("Monetary Policy", "HIGH", "the central bank's policy rate", ("bonds", "banks", "currency"),
     r"\b(MPC|monetary policy|policy rate|central bank rate|CBR|repo rate|interest rate decision)\b"
     r"|sera ya fedha|riba ya benki kuu"),
    ("Inflation", "HIGH", "consumer price inflation", ("bonds", "currency"),
     r"\b(inflation|consumer price|CPI)\b|mfumuko wa bei"),
    ("FX", "HIGH", "foreign exchange rules or rates", ("currency", "banks"),
     r"\b(foreign exchange|exchange rate|forex|FX|shilling|dollar)\b|fedha za kigeni"),
    ("Fiscal Policy", "HIGH", "government budget or borrowing", ("bonds",),
     r"\b(budget|fiscal|public debt|eurobond|tax(es|ation)?)\b|bajeti"),
    ("Bonds", "MEDIUM", "government securities issuance", ("bonds",),
     r"\b(treasury (bond|bill)s?|T-bills?|government securities|bond auction|auction calendar|yield curve)\b"
     r"|dhamana za serikali"),
    ("Banking", "MEDIUM", "bank licensing or supervision", ("banks",),
     r"(?<!central )(?<!world )\bbanks?\b|\b(bank supervision|banking|licen[cs]e[sd]?|microfinance bank|capital adequacy|prudential)\b"
     r"|leseni|benki(?! kuu)"),
    ("GDP", "MEDIUM", "economic growth", ("equities", "bonds"),
     r"\b(GDP|economic growth|economic outlook|economic update|recession)\b|pato la taifa"),
    ("Trade", "LOW", "trade and the current account", ("currency",),
     r"\b(exports?|imports?|trade (deficit|balance|logistics)|current account|tariffs?)\b"),
    ("Commodities", "LOW", "commodity prices", ("equities", "currency"),
     r"\b(oil|gold|coffee|tea|cotton|commodit(y|ies)|fuel prices?)\b"),
    ("Infrastructure", "LOW", "infrastructure investment", ("equities",),
     r"\b(infrastructure|railway|SGR|port|corridor|pipeline|power project|energy project)\b"),
    ("Payments", "LOW", "payment-system regulation", ("banks",),
     r"\b(payment system|mobile money|fintech|sandbox)\b|teknolojia ya fedha|majaribio ya teknolojia"),
    ("Regional Economy", "LOW", "regional economic policy", ("currency",),
     r"\b(EAC|East African Community|regional integration)\b|jumuiya ya afrika mashariki|EAC"),
]
COUNTRY_PATTERNS = {"TZ": r"\b(Tanzania|Tanzanian|Dar es Salaam|Zanzibar)\b",
                    "KE": r"\b(Kenya|Kenyan|Nairobi)\b", "UG": r"\b(Uganda|Ugandan|Kampala)\b"}
LEVEL_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class Tagged:
    categories: list[str]
    countries: list[str]
    relevance: str
    relevance_reason: str
    related: dict = field(default_factory=dict)


def _country_list(codes: list[str]) -> str:
    names = [COUNTRY_NAMES[c] for c in codes]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def classify(title: str, *, source_country: str | None, summary: str | None = None,
             securities: list[dict] | None = None) -> Tagged:
    """Tag one headline. `securities` is the security master as dicts (id, name, ticker, exchange, sector,
    country_code); `source_country` is the publisher's home country when it is a national institution."""
    text = f"{title} {summary or ''}"
    cats, best, best_rule = [], None, None
    for cat, level, variable, assets, pattern in RULES:
        if re.search(pattern, text, re.I):
            if cat not in cats:
                cats.append(cat)
            if level and (best is None or LEVEL_ORDER[level] > LEVEL_ORDER[best]):
                best, best_rule = level, (variable, assets)
    countries = [c for c, p in COUNTRY_PATTERNS.items() if re.search(p, text, re.I)]
    if source_country and source_country not in countries:
        countries.insert(0, source_country)

    if best is None or not countries:
        reason = ("Impact not assessed: the headline names no economic variable AfriEdge tracks."
                  if best is None else
                  "Impact not assessed: the story is not tied to Tanzania, Kenya or Uganda.")
        return Tagged(cats, countries, "NOT_ASSESSED", reason, _related(cats, countries, title, securities, None))

    variable, assets = best_rule
    reason = (f"Potential impact assessed from the affected asset class ({', '.join(assets)}), the geography "
              f"({_country_list(countries)}) and the disclosed economic variable ({variable}).")
    return Tagged(cats, countries, best, reason, _related(cats, countries, title, securities, assets))


def _related(cats: list[str], countries: list[str], title: str, securities: list[dict] | None,
             assets: tuple[str, ...] | None) -> dict:
    markets = [{"country": c, "exchange": EXCHANGE[c], "currency": CURRENCY[c]} for c in countries]
    indicators: list[dict] = []
    for c in countries:
        iso = WB_ISO3[c]
        if "Inflation" in cats or "Monetary Policy" in cats:
            indicators.append({"series_id": f"WB_{iso}_FP.CPI.TOTL.ZG", "label": f"{COUNTRY_NAMES[c]} inflation"})
        if "FX" in cats or "Monetary Policy" in cats:
            indicators.append({"series_id": f"WB_{iso}_PA.NUS.FCRF",
                               "label": f"{CURRENCY[c]} per US dollar (annual average)"})
        if "GDP" in cats:
            indicators.append({"series_id": f"WB_{iso}_NY.GDP.MKTP.KD.ZG", "label": f"{COUNTRY_NAMES[c]} GDP growth"})
        if c == "TZ" and ("Monetary Policy" in cats):
            indicators.append({"series_id": "BOT_CBR", "label": "Bank of Tanzania Central Bank Rate"})
        if c == "TZ" and ("Bonds" in cats or "Monetary Policy" in cats or "Fiscal Policy" in cats):
            indicators.append({"series_id": "BOT_TBOND_15Y_WAYTM", "label": "Tanzania 15-year bond yield"})

    companies: list[dict] = []
    for s in securities or []:
        named = re.search(rf"\b{re.escape(s['ticker'])}\b", title) or (
            len(s["name"]) > 6 and re.search(re.escape(_short_name(s["name"])), title, re.I))
        if named:
            companies.append({"security_id": s["id"], "name": s["name"], "link": "named",
                              "why": "The company is named in the headline."})
    if assets and "banks" in assets and ({"Monetary Policy", "Banking"} & set(cats)):
        for s in securities or []:
            if s.get("sector") == "Banking" and s.get("country_code") in countries and \
                    not any(x["security_id"] == s["id"] for x in companies):
                companies.append({"security_id": s["id"], "name": s["name"], "link": "sector",
                                  "why": f"Sector link: a listed bank in {COUNTRY_NAMES[s['country_code']]}, where "
                                         f"the story concerns {'monetary policy' if 'Monetary Policy' in cats else 'banking'}."})
    return {"markets": markets, "indicators": indicators, "companies": companies}


def _short_name(name: str) -> str:
    """'NMB Bank Plc' -> 'NMB Bank'; trailing legal forms are not distinctive."""
    return re.sub(r"\s+(Plc|PLC|Limited|Ltd\.?|Holdings|Group)\.?$", "", name).strip()
