"""The copilot's answer format, and the deterministic check that decides whether an answer may be shown.

An answer is shown only if
  1. every statement cites at least one context key, and every cited key exists;
  2. every number in a source-fact or calculated statement matches a value of an entry it cites (as written,
     or as a percentage), to the precision the answer wrote it;
  3. an interpretation introduces no number that is not in the entries it cites.
Otherwise the whole answer is withheld as UNGROUNDED. Showing it "with a warning" would still put a number
in front of a reader that no source supports. Years, and small counts up to 12, are not treated as figures.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, Field

# A number starts at a word boundary: not inside "FY2025" (which would otherwise yield "025") or a key.
# Nor after a hyphen joined to a word ("RA-20261007-001"); a free-standing "-5" is still a number.
NUMBER = re.compile(r"(?<![A-Za-z_.\d])(?<![A-Za-z\d]-)-?\d[\d,]*(?:\.\d+)?")


class Statement(BaseModel):
    text: str = Field(description="One sentence. Numbers must be written exactly as in the cited entries' display text.")
    keys: list[str] = Field(description="The context entry keys this sentence is based on (at least one).")


class Answer(BaseModel):
    answerable: bool = Field(description="False if the context does not contain what the question needs.")
    source_facts: list[Statement] = Field(description="What the documents and the exchange report, from SOURCE_FACT entries.")
    calculated_results: list[Statement] = Field(description="Results of the deterministic engines, from CALCULATED entries.")
    interpretation: list[Statement] = Field(description="Your reading of what the facts and results mean. No new numbers.")
    unavailable: list[str] = Field(description="What the question asked for that the context does not contain, and why (from STATUS entries).")


def _numbers(text: str) -> list[tuple[Decimal, int]]:
    """Numbers in a text, with the count of decimals written (the precision the writer claimed)."""
    out = []
    for raw in NUMBER.findall(text):
        clean = raw.replace(",", "")
        try:
            value = Decimal(clean)
        except InvalidOperation:
            continue
        if value == value.to_integral_value() and (Decimal(0) <= value <= 12 or Decimal(1990) <= value <= 2100):
            continue                      # counts ("three scenarios" as 3) and years are not figures
        places = len(clean.split(".")[1]) if "." in clean else 0
        out.append((value, places))
    return out


def _supported(n: Decimal, places: int, entries: list[dict]) -> bool:
    tolerance = Decimal(1).scaleb(-places) / 2          # 9.0 claims 9.0 +/- 0.05
    for e in entries:
        candidates = [n2 for n2, _ in _numbers(e.get("display", ""))]
        if e.get("value") is not None:
            try:
                v = Decimal(e["value"])
                candidates += [v, v * 100]
            except InvalidOperation:
                pass
        if any(abs(abs(n) - abs(c)) <= tolerance for c in candidates):
            return True
    return False


def check(answer: Answer, context: dict, question: str = "") -> list[str]:
    """Problems that make the answer unshowable; an empty list means it is grounded."""
    by_key = {e["key"]: e for e in context["entries"]}
    asked = {n for n, _ in _numbers(question)}
    problems = []
    for section in ("source_facts", "calculated_results", "interpretation"):
        for st in getattr(answer, section):
            if not st.keys:
                problems.append(f"{section}: '{st.text[:60]}' cites no context entry")
                continue
            missing = [k for k in st.keys if k not in by_key]
            if missing:
                problems.append(f"{section}: cites keys that do not exist: {missing}")
                continue
            cited = [by_key[k] for k in st.keys]
            for n, places in _numbers(st.text):
                if n in asked:
                    continue                   # the user's own number, repeated back
                if not _supported(n, places, cited):
                    problems.append(f"{section}: the number {n} in '{st.text[:80]}' is not in the cited entries {st.keys}")
    return problems
