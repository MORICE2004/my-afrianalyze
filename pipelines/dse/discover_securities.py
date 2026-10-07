r"""Discover DSE-listed securities from the exchange's own pages, instead of a hand-made list.

    .venv\Scripts\python -m pipelines.dse.discover_securities

Sources (robots.txt allows both; the owner approved using dse.co.tz on 2026-09-19):
  1. https://dse.co.tz/listed/company/list         code and profile link for every listed company
  2. https://dse.co.tz/api/get/live/market/prices  the codes quoted today
Each profile page is read for the company name only, with a strict pattern (the first "... PLC" / "...
Limited" phrase). Nothing is inferred: when the pattern does not match, the name stays the code. The DSE does
not publish sector or ISIN in structured form, so they are left unclassified rather than guessed.

Entries already in the security master (config/securities.json, each verified by hand) are never changed.
The raw list page is stored with its SHA-256, and data_source_status 'dse_issuers' records the run.
"""
from __future__ import annotations

import hashlib
import html
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from packages.database.models import DataSourceStatus, Security
from packages.database.session import SessionLocal

UA = {"User-Agent": "Mozilla/5.0 (AfriEdge research; security master discovery)"}
LIST_URL = "https://dse.co.tz/listed/company/list"
LIVE_URL = "https://dse.co.tz/api/get/live/market/prices"
STORE = Path("data/raw/dse/public")
ROW = re.compile(r"<tr[^>]*>\s*<td[^>]*>\s*(\d+)\s*</td>\s*<td[^>]*>\s*([A-Z0-9\-]{2,12})\s*</td>.*?"
                 r'href="(https://dse\.co\.tz/listed/company/profile\?id=\d+)"', re.S)
# The name must OPEN the profile ("CRDB Bank PLC is ..."). A match later in the prose was found to pick up
# other companies (KCB's profile mentions the exchange, so it read "Dar Es Salaam Stock Exchange PLC").
NAME = re.compile(r"^(?:The\s+)?((?:[A-Z][A-Za-z&'\-\.]*\s){0,6}?(?:PLC|Plc|plc|Limited|LIMITED|Ltd)(?:\s+Company)?)\b")


def parse_list(page: str) -> list[tuple[str, str]]:
    """(code, profile url) for each row of the listed-company table."""
    return [(code, url) for _, code, url in ROW.findall(page)]


def profile_text(page: str) -> str:
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)))
    i = text.find(" Profile ")
    return text[i + 9:i + 1500] if i >= 0 else ""


def name_from_profile(text: str) -> str | None:
    """The first company-name phrase in the profile's own words, or None. Not a guess: a strict pattern."""
    m = NAME.match(text.strip())
    if not m:
        return None
    name = m.group(1).strip()
    # A profile that opens with a section heading ("HISTORICAL BACKGROUND Mwalimu ...") is not a name.
    if re.search(r"\b(HISTORICAL|HISTORY|BACKGROUND|PROFILE|INTRODUCTION|OVERVIEW|ABOUT)\b", name, re.I):
        return None
    return name if 2 <= len(name.split()) <= 8 else None


def main() -> int:
    now = datetime.now(timezone.utc)
    page = requests.get(LIST_URL, headers=UA, timeout=60)
    page.raise_for_status()
    rows = parse_list(page.text)
    live = requests.get(LIVE_URL, headers=UA, timeout=60).json().get("data") or []
    quoted = {str(r.get("company", "")).upper() for r in live}
    if len(rows) < 10:
        print(f"Only {len(rows)} rows parsed from {LIST_URL}; the page layout may have changed. Nothing written.")
        return 1

    STORE.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(page.content).hexdigest()
    (STORE / f"dse_listed_companies_{sha[:12]}.html").write_bytes(page.content)

    # Read every profile first: a name claimed by two codes means one profile describes another company
    # (on 2026-10-07 the TTP profile carried TOL Gases' text), so neither gets that name.
    names: dict[str, str | None] = {}
    for code, profile in rows:
        time.sleep(0.5)
        try:
            names[code] = name_from_profile(profile_text(requests.get(profile, headers=UA, timeout=60).text))
        except requests.RequestException:
            names[code] = None
    seen: dict[str, list[str]] = {}
    for code, n in names.items():
        if n:
            seen.setdefault(n.lower(), []).append(code)
    clashes = {c for codes in seen.values() if len(codes) > 1 for c in codes}
    for c in clashes:
        names[c] = None

    added, kept, unnamed = [], [], []
    with SessionLocal() as s:
        for code, profile in rows:
            sid = f"DSE:{code}"
            if s.get(Security, sid) is not None:
                kept.append(code)
                continue
            name = names[code]
            if name is None:
                unnamed.append(code)
            s.add(Security(
                id=sid, exchange="DSE", local_ticker=code, isin=None, name=name or code,
                sector="Unclassified", currency="TZS", is_bank=False, industry_template="unclassified",
                listing_status="listed", listing_url=profile, verified_at=date.today(),
                verification_note=(f"Discovered {now:%Y-%m-%d} from the DSE listed-company page (sha256 {sha[:12]})"
                                   + ("; quoted on the DSE live price list that day" if code in quoted else
                                      "; NOT on the DSE live price list that day")
                                   + ("; name read from the opening words of the DSE profile" if name else
                                      "; the same profile text appears under another code, so no name is taken"
                                      if code in clashes else
                                      "; the DSE profile does not open with a company name, so the code is shown")
                                   + ". Sector and ISIN are not published by the DSE in structured form.")))
            added.append(code)
        s.merge(DataSourceStatus(
            source="dse_issuers", last_success_at=now, last_attempt_at=now, status="ok", max_age_hours=24 * 35,
            detail=f"{len(rows)} listed companies on the DSE list page, {len(quoted)} quoted on the live price list; "
                   f"{len(added)} added, {len(kept)} already verified by hand. Source: {LIST_URL}"))
        s.commit()
    print(f"{len(rows)} listed on the DSE page; {len(quoted)} quoted today. Added {len(added)}: {', '.join(added)}.")
    print(f"Kept {len(kept)} hand-verified entries unchanged: {', '.join(kept)}.")
    if unnamed:
        print(f"No name found in the profile text for: {', '.join(unnamed)} (shown by code).")
    not_quoted = [c for c, _ in rows if c not in quoted]
    if not_quoted:
        print(f"On the list page but not on today's live price list: {', '.join(not_quoted)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
