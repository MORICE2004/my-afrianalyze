r"""Official macro and reference inputs for Tanzania.

  * BoT Treasury bond auction results (weighted average yield to maturity)
      https://www.bot.go.tz/TBonds  +  POST /TBonds/AuctionSummaries
  * BoT Central Bank Rate, from the latest Monetary Policy Committee statement found
  * NBS headline inflation, from the monthly CPI release
  * Damodaran country risk premium table (NYU Stern)

Every raw response is saved under data/raw/ with a SHA-256 so each stored value
can be traced to the exact bytes it came from.

    .venv\Scripts\python -m pipelines.macro
"""
from __future__ import annotations

import hashlib
import html
import json
import io
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import requests

from packages.database.models import DataSourceStatus, MacroObservation, ReferenceInput
from packages.database.session import SessionLocal

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0 Safari/537.36"}
RAW = Path("data/raw")

BOT_TBONDS = "https://www.bot.go.tz/TBonds"
BOT_TBOND_SUMMARY = "https://www.bot.go.tz/TBonds/AuctionSummaries"
# The newest MPC statement is found on this page each run (bot_cbr), not pinned to one PDF.
BOT_PRESS_RELEASES = "https://www.bot.go.tz/PressRelease?lang=en"
NBS_CPI_PAGE = "https://www.nbs.go.tz/statistics/topic/consumer-price-index-2026"
DAMODARAN_CRP = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html"
DAMODARAN_BETAS = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaemerg.xls"
# The industry whose average beta stands in for a Tanzanian bank. NMB and CRDB are deposit-taking
# commercial banks serving one country, which is what "Banks (Regional)" covers in this dataset.
DAMODARAN_BANK_INDUSTRY = "Banks (Regional)"


def now() -> datetime:
    return datetime.now(timezone.utc)


def save(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def status(session, source: str, ok: bool, max_age_hours: int, detail: str) -> None:
    row = session.get(DataSourceStatus, source) or DataSourceStatus(source=source)
    row.last_attempt_at = now()
    if ok:
        row.last_success_at = row.last_attempt_at
    row.status = "ok" if ok else "failed"
    row.max_age_hours = max_age_hours
    row.detail = detail
    session.merge(row)


def upsert_obs(session, **kw) -> None:
    existing = session.query(MacroObservation).filter_by(
        series_id=kw["series_id"], observation_date=kw["observation_date"], label=kw["label"]).one_or_none()
    if existing:
        for k, v in kw.items():
            setattr(existing, k, v)
    else:
        session.add(MacroObservation(**kw))


# ------------------------------------------------------------------ BoT bonds

def bot_bonds(session) -> str:
    resp = requests.get(BOT_TBONDS, headers=UA, timeout=60)
    resp.raise_for_status()
    save(RAW / "bot" / "tbonds_list.html", resp.content)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", resp.text, re.S)
    latest_by_tenor: dict[int, tuple[date, str]] = {}
    for r in rows:
        title = re.search(r"(\d+(?:\.\d+)?)%\s*(\d+)-YEAR TREASURY BOND", r)
        when = re.search(r"(\d{2}-[A-Z]{3}-\d{4})", r)
        button = re.search(r'value="(\d+_\d+)"', r)
        if not (title and when and button):
            continue
        tenor = int(title.group(2))
        d = datetime.strptime(when.group(1), "%d-%b-%Y").date()
        if tenor not in latest_by_tenor or d > latest_by_tenor[tenor][0]:
            latest_by_tenor[tenor] = (d, button.group(1))
    loaded = []
    for tenor, (d, key) in sorted(latest_by_tenor.items()):
        au_no, au_days = key.split("_")
        r = requests.post(BOT_TBOND_SUMMARY, data={"au_no": au_no, "au_days": au_days}, headers=UA, timeout=60)
        r.raise_for_status()
        payload = r.json()
        if not str(payload.get("message", "")).upper().startswith("SUCCESS"):
            continue
        sha = save(RAW / "bot" / f"tbond_{tenor}y_{au_no}_{d.isoformat()}.json", r.content)
        items = {i["itemDesc"]: i["itemValue"] for i in payload["tbondSummary"]}
        ytm = items.get("WEIGHTED AVERAGE YIELD-TO-MATURITY")
        if ytm is None:
            continue
        upsert_obs(session, series_id=f"BOT_TBOND_{tenor}Y_WAYTM", observation_date=d, published_on=d,
                   value=Decimal(ytm) / 100, unit="decimal",
                   label=f"{payload['bondTitle']} - weighted average yield to maturity",
                   attributes={"auction_number": au_no, "isin": payload.get("ISIN"),
                               "redemption_date": items.get("REDEMPTION DATE"),
                               "weighted_average_price": items.get("WEIGHTED AVERAGE PRICE (WAP) FOR SUCCESSFUL BIDS"),
                               "raw_sha256": sha, "request": {"au_no": au_no, "au_days": au_days}},
                   source_url=f"{BOT_TBONDS} (Auction {au_no}, {payload['BondDate']})",
                   source_name="Bank of Tanzania, Treasury Bonds Auction Results", retrieved_at=now())
        loaded.append(f"{tenor}Y {Decimal(ytm):.4f}% on {d}")
    status(session, "bot_tbonds", bool(loaded), 24 * 21, "; ".join(loaded) or "no auctions parsed")
    return "BoT bonds: " + "; ".join(loaded)


# ------------------------------------------------------------------ BoT CBR

def _pdf_text(content: bytes) -> str:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(io.BytesIO(content))
    return re.sub(r"\s+", " ", " ".join(doc[i].get_textpage().get_text_range() for i in range(len(doc))))


CBR_DECISION = re.compile(
    r"(maintained|kept|retained|raised|increased|lowered|reduced|cut)\s+the\s+Central\s+Bank\s+Rate\s*\(CBR\)\s+"
    r"(?:(?:at|from)\s+([\d.]+)\s*(?:percent|%)\s*)?(?:to\s+([\d.]+)\s*(?:percent|%))?", re.I)


def latest_mpc_statement() -> tuple[str, date]:
    """The newest Monetary Policy Committee statement listed on the BoT's public notices page. The PDF names
    start with their publication time (e.g. 2026070313025546 = 3 July 2026), so the newest sorts last."""
    r = requests.get(BOT_PRESS_RELEASES, headers=UA, timeout=60)
    r.raise_for_status()
    found = []
    for href, label in re.findall(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', r.text, re.S | re.I):
        text = html.unescape(re.sub(r"<[^>]+>", " ", label)).lower()
        stamp = re.search(r"/(\d{8})\d*\.pdf$", href)
        if "monetary policy committee" in text and "calendar" not in text and stamp:
            found.append((stamp.group(1), href))
    if not found:
        raise ValueError(f"No MPC statement listed on {BOT_PRESS_RELEASES}; the page layout may have changed")
    stamp, href = max(found)
    url = href if href.startswith("http") else "https://www.bot.go.tz" + href
    return url, date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))


def bot_cbr(session) -> str:
    """The policy rate from the newest MPC statement. If that statement cannot be read, the job fails: an
    older statement's rate is never carried forward as if it were current."""
    url, published = latest_mpc_statement()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    sha = save(RAW / "bot" / f"mpc_statement_{published.isoformat()}.pdf", r.content)
    text = " ".join(_pdf_text(r.content).split())
    m = CBR_DECISION.search(text)
    rate = (m.group(3) or m.group(2)) if m else None
    if not rate:
        status(session, "bot_cbr", False, 24 * 100, f"CBR decision sentence not found in the newest MPC statement ({url})")
        return "BoT CBR: decision not found in the newest statement"
    meeting = re.search(r"[Mm]eeting held on (\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(20\d\d)", text)
    obs_date = published
    if meeting:
        try:
            obs_date = datetime.strptime(" ".join(meeting.groups()), "%d %B %Y").date()
        except ValueError:
            pass
    upsert_obs(session, series_id="BOT_CBR", observation_date=obs_date, value=Decimal(rate) / 100,
               unit="decimal", label=f"Central Bank Rate (policy rate), MPC decision of {obs_date.isoformat()}",
               attributes={"quote": m.group(0).strip(), "decision": m.group(1).lower(),
                           "published": published.isoformat(), "raw_sha256": sha},
               source_url=url, source_name="Bank of Tanzania, Monetary Policy Committee Statement",
               retrieved_at=now())
    # The MPC meets quarterly; past ~100 days a newer decision should exist.
    stale = (date.today() - obs_date).days > 100
    status(session, "bot_cbr", not stale, 24 * 100,
           f"CBR {rate}% ({m.group(1).lower()}) at the MPC meeting of {obs_date.isoformat()}"
           + ("; stale: a newer MPC decision is expected but is not listed yet" if stale else ""))
    return f"BoT CBR: {rate}% ({m.group(1).lower()}, {obs_date.isoformat()}){' STALE' if stale else ''}"


# ------------------------------------------------------------------ NBS CPI

def nbs_inflation(session) -> str:
    page = requests.get(NBS_CPI_PAGE, headers=UA, timeout=60)
    page.raise_for_status()
    links = re.findall(r'href="([^"]*CPI(?:\s|%20)*Release_(\d{2})(\d{4})_English\.pdf)"', page.text)
    if not links:
        status(session, "nbs_cpi", False, 24 * 45, "No CPI release link found")
        return "NBS CPI: no release link"
    url, mm, yyyy = max(links, key=lambda l: (l[2], l[1]))
    url = html.unescape(url).replace(" ", "%20")
    if url.startswith("/"):
        url = "https://www.nbs.go.tz" + url
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    sha = save(RAW / "nbs" / f"cpi_release_{yyyy}-{mm}.pdf", r.content)
    text = _pdf_text(r.content)
    m = re.search(r"headline inflation rate[^.]{0,80}?(?:has |)(?:increased|decreased|remained|stood|was)[^.]{0,40}?"
                  r"(?:to|at) ([\d.]+) percent", text, re.I)
    if not m:
        m = re.search(r"annual headline inflation rate[^.]{0,120}?([\d.]+) percent", text, re.I)
    if not m:
        status(session, "nbs_cpi", False, 24 * 45, f"Headline rate sentence not found in {url}")
        return "NBS CPI: sentence not found"
    obs = date(int(yyyy), int(mm), 1)
    upsert_obs(session, series_id="NBS_CPI_HEADLINE_YOY", observation_date=obs, value=Decimal(m.group(1)) / 100,
               unit="decimal", label=f"Headline inflation, year-on-year, {obs:%B %Y}",
               attributes={"quote": m.group(0)[:300], "raw_sha256": sha},
               source_url=url, source_name="National Bureau of Statistics Tanzania, National CPI release",
               retrieved_at=now())
    status(session, "nbs_cpi", True, 24 * 45, f"{obs:%B %Y}: {m.group(1)}%")
    return f"NBS CPI: {m.group(1)}% ({obs:%B %Y})"


# ------------------------------------------------------------------ Damodaran

def damodaran(session) -> str:
    r = requests.get(DAMODARAN_CRP, headers=UA, timeout=60)
    r.raise_for_status()
    sha = save(RAW / "reference" / "damodaran_ctryprem.html", r.content)
    text = r.content.decode("latin-1")
    flat = html.unescape(re.sub(r"<[^>]+>", "|", text))
    flat = re.sub(r"[ \t\r\n]+", " ", flat)
    flat = re.sub(r"(\s*\|\s*)+", "|", flat)
    updated = re.search(r"Last updated:\s*([A-Za-z]+ \d{1,2}, \d{4})", flat)
    as_of = datetime.strptime(updated.group(1), "%B %d, %Y").date() if updated else None
    header = "Country|Moody's rating|Adj. Default Spread|Country Risk Premium|Equity Risk Premium|Corporate Tax Rate"
    if header not in flat or as_of is None:
        status(session, "damodaran_crp", False, 24 * 200, "Table header or update date not found; layout changed")
        return "Damodaran: layout changed, nothing loaded"

    def row(country: str) -> list[str]:
        m = re.search(rf"\|{re.escape(country)}\|([^|]+)\|([\d.]+)%\|([\d.]+)%\|([\d.]+)%\|([\d.]+)%", flat)
        if not m:
            raise ValueError(f"{country} row not found")
        return list(m.groups())

    tz = row("Tanzania")
    us = row("United States")
    mature_tz = Decimal(tz[3]) - Decimal(tz[2])
    mature_us = Decimal(us[3]) - Decimal(us[2])
    if abs(mature_tz - mature_us) > Decimal("0.01"):
        status(session, "damodaran_crp", False, 24 * 200,
               f"Mature ERP inconsistent: TZ {mature_tz:.2f} vs US {mature_us:.2f}")
        return "Damodaran: inconsistent mature ERP, nothing loaded"
    base = dict(source_name=f"Aswath Damodaran, Country Default Spreads and Risk Premiums (updated {as_of:%d %B %Y})",
                source_url=DAMODARAN_CRP, as_of=as_of, retrieved_at=now(),
                file_path="data/raw/reference/damodaran_ctryprem.html", sha256=sha)
    rows = [
        ("TZ_DEFAULT_SPREAD", Decimal(tz[1]) / 100, "decimal", f"Tanzania adjusted sovereign default spread (Moody's {tz[0]})"),
        ("TZ_COUNTRY_RISK_PREMIUM", Decimal(tz[2]) / 100, "decimal", "Tanzania country risk premium"),
        ("TZ_TOTAL_ERP", Decimal(tz[3]) / 100, "decimal", "Tanzania total equity risk premium"),
        ("TZ_CORPORATE_TAX_RATE", Decimal(tz[4]) / 100, "decimal", "Tanzania corporate tax rate"),
        ("MATURE_MARKET_ERP", round(mature_tz, 4) / 100, "decimal",
         "Mature-market ERP (Tanzania total ERP minus CRP; equals US ERP minus US CRP)"),
    ]
    for key, value, unit, label in rows:
        session.merge(ReferenceInput(key=key, value=value, unit=unit, label=label, **base))
    status(session, "damodaran_crp", True, 24 * 200, f"Tanzania {tz[0]}, CRP {tz[2]}%, as of {as_of}")
    return f"Damodaran: Tanzania {tz[0]} spread {tz[1]}% CRP {tz[2]}% ERP {tz[3]}%, mature {mature_tz:.2f}% ({as_of})"


def damodaran_industry_beta(session) -> str:
    """The average beta of emerging-market banks, used where a local regression cannot be trusted.

    A DSE bank does not trade every day, so a beta regressed on its own price history is pulled toward
    zero and swings with the measurement interval (NMB: 0.02 daily, 0.79 monthly). An average across
    many listed banks does not have that problem. The owner chose this basis on 2026-09-20.

    Damodaran's levered industry beta is stored and used as published. His unlevered figures are stored
    too, but unlevering and relevering a bank is not reliable: for a bank, deposits are not debt in the
    way the Hamada formula assumes, and he says so himself. The relevered figure is shown on the report
    as a cross-check, never as the valuation input.
    """
    import xlrd                                  # only this job needs it

    r = requests.get(DAMODARAN_BETAS, headers=UA, timeout=120)
    r.raise_for_status()
    sha = save(RAW / "reference" / "damodaran_betaemerg.xls", r.content)
    book = xlrd.open_workbook(file_contents=r.content)
    if "Industry Averages" not in book.sheet_names():
        status(session, "damodaran_industry_beta", False, 24 * 200, "Sheet 'Industry Averages' not found")
        return "Damodaran betas: layout changed, nothing loaded"
    sheet = book.sheet_by_name("Industry Averages")

    header_row = next((i for i in range(sheet.nrows)
                       if str(sheet.cell_value(i, 0)).strip() == "Industry Name"), None)
    if header_row is None:
        status(session, "damodaran_industry_beta", False, 24 * 200, "Header row not found")
        return "Damodaran betas: layout changed, nothing loaded"
    columns = {str(sheet.cell_value(header_row, j)).strip().rstrip(":").lower(): j
               for j in range(sheet.ncols)}

    def column(*names: str) -> int | None:
        for wanted in names:
            for label, j in columns.items():
                if label.startswith(wanted.lower()):
                    return j
        return None

    wanted = {"beta": column("beta"), "firms": column("number of firms"), "de": column("d/e ratio"),
              "tax": column("effective tax rate"), "unlevered": column("unlevered beta"),
              "unlevered_cash": column("unlevered beta corrected for c")}
    if any(v is None for v in wanted.values()):
        missing = [k for k, v in wanted.items() if v is None]
        status(session, "damodaran_industry_beta", False, 24 * 200, f"Columns not found: {missing}")
        return f"Damodaran betas: columns {missing} not found, nothing loaded"

    row_index = next((i for i in range(sheet.nrows)
                      if str(sheet.cell_value(i, 0)).strip() == DAMODARAN_BANK_INDUSTRY), None)
    if row_index is None:
        status(session, "damodaran_industry_beta", False, 24 * 200,
               f"Industry '{DAMODARAN_BANK_INDUSTRY}' not found")
        return f"Damodaran betas: '{DAMODARAN_BANK_INDUSTRY}' not found, nothing loaded"

    def cell(key: str) -> Decimal:
        return Decimal(str(sheet.cell_value(row_index, wanted[key])))

    as_of = None
    for i in range(min(8, sheet.nrows)):
        if "date updated" in str(sheet.cell_value(i, 0)).strip().lower():
            as_of = xlrd.xldate_as_datetime(float(sheet.cell_value(i, 1)), book.datemode).date()
            break
    if as_of is None:
        status(session, "damodaran_industry_beta", False, 24 * 200, "Update date not found")
        return "Damodaran betas: update date not found, nothing loaded"

    beta = round(cell("beta"), 4)
    firms = int(cell("firms"))
    if not (Decimal("0.1") < beta < Decimal("3")) or firms < 20:
        status(session, "damodaran_industry_beta", False, 24 * 200,
               f"Implausible: beta {beta} across {firms} firms")
        return f"Damodaran betas: beta {beta} across {firms} firms is not usable, nothing loaded"

    base = dict(source_name=f"Aswath Damodaran, Betas by Sector, Emerging Markets, "
                            f"{DAMODARAN_BANK_INDUSTRY} ({firms} firms, updated {as_of:%d %B %Y})",
                source_url=DAMODARAN_BETAS, as_of=as_of, retrieved_at=now(),
                file_path="data/raw/reference/damodaran_betaemerg.xls", sha256=sha)
    rows = [
        ("EM_BANK_INDUSTRY_BETA", beta, "decimal",
         f"Average levered beta of {firms} emerging-market regional banks"),
        ("EM_BANK_INDUSTRY_FIRMS", Decimal(firms), "count",
         f"Firms behind the {DAMODARAN_BANK_INDUSTRY} average"),
        ("EM_BANK_INDUSTRY_DE_RATIO", round(cell("de"), 4), "ratio",
         f"Average debt to equity of the {DAMODARAN_BANK_INDUSTRY} group"),
        ("EM_BANK_INDUSTRY_TAX_RATE", round(cell("tax"), 4), "decimal",
         f"Average effective tax rate of the {DAMODARAN_BANK_INDUSTRY} group"),
        ("EM_BANK_INDUSTRY_UNLEVERED_BETA", round(cell("unlevered"), 4), "decimal",
         "Unlevered beta of the group (cross-check only; unlevering a bank is unreliable)"),
        ("EM_BANK_INDUSTRY_UNLEVERED_BETA_CASH_ADJ", round(cell("unlevered_cash"), 4), "decimal",
         "Unlevered beta corrected for cash (cross-check only)"),
    ]
    for key, value, unit, label in rows:
        session.merge(ReferenceInput(key=key, value=value, unit=unit, label=label, **base))
    status(session, "damodaran_industry_beta", True, 24 * 200,
           f"{DAMODARAN_BANK_INDUSTRY}: levered beta {beta} across {firms} firms, as of {as_of}")
    return (f"Damodaran betas: {DAMODARAN_BANK_INDUSTRY} levered beta {beta} "
            f"({firms} firms, D/E {cell('de'):.2f}, as of {as_of})")



# ------------------------------------------------------------------ World Bank (CC BY 4.0)

WB_API = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}?format=json&per_page=500&date=2010:2030"
WB_COUNTRIES = ("TZA", "KEN", "UGA")
# indicator -> (label, unit stored, divisor, plausible range of the stored value)
WB_INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": ("Real GDP growth (annual)", "decimal", 100, (-0.3, 0.3)),
    "FP.CPI.TOTL.ZG": ("Consumer price inflation (annual)", "decimal", 100, (-0.1, 2.0)),
    "BN.CAB.XOKA.GD.ZS": ("Current account balance (share of GDP)", "decimal", 100, (-0.5, 0.5)),
    "PA.NUS.FCRF": ("Official exchange rate (local currency per US dollar, period average)", "LCU_per_USD", 1, (0.01, 100000)),
}


def world_bank(session) -> str:
    """Annual macro indicators for Tanzania, Kenya and Uganda from the World Bank API. Values are parsed as exact
    decimals (never floats); a year the World Bank leaves empty stays absent; a value outside its plausible
    range stops the job rather than being stored. Licence: CC BY 4.0 (datacatalog.worldbank.org/public-licenses)."""
    stored, missing = 0, 0
    latest: dict[str, str] = {}
    for indicator, (label, unit, divisor, (lo, hi)) in WB_INDICATORS.items():
        url = WB_API.format(countries=";".join(WB_COUNTRIES), indicator=indicator)
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        payload = json.loads(r.text, parse_float=Decimal)
        if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
            raise ValueError(f"World Bank answer for {indicator} has an unexpected shape")
        meta, rows = payload[0], payload[1]
        updated = meta.get("lastupdated")
        for row in rows:
            iso3, year, raw = row.get("countryiso3code"), row.get("date"), row.get("value")
            if iso3 not in WB_COUNTRIES or not str(year).isdigit():
                continue
            if raw is None:
                missing += 1
                continue
            value = Decimal(str(raw)) / divisor
            if not (Decimal(str(lo)) <= value <= Decimal(str(hi))):
                raise ValueError(f"{indicator} {iso3} {year} = {raw} is outside the plausible range; not stored")
            upsert_obs(session, series_id=f"WB_{iso3}_{indicator}", observation_date=date(int(year), 12, 31),
                       published_on=date.fromisoformat(updated) if updated else None, value=value, unit=unit,
                       label=f"{row['country']['value']}: {label}, {year}",
                       attributes={"indicator": indicator, "indicator_name": row["indicator"]["value"],
                                   "country": iso3, "year": int(year), "as_published": str(raw),
                                   "licence": "CC BY 4.0", "source_last_updated": updated},
                       source_url=url, source_name="World Bank, World Development Indicators", retrieved_at=now())
            stored += 1
            key = f"{iso3} {indicator}"
            latest[key] = max(latest.get(key, ""), str(year))
    newest = max(latest.values()) if latest else "none"
    status(session, "world_bank", True, 24 * 120,
           f"{stored} annual observations for {', '.join(WB_COUNTRIES)} across {len(WB_INDICATORS)} indicators "
           f"(latest year {newest}); {missing} country-years the World Bank leaves empty. CC BY 4.0.")
    return f"World Bank: {stored} observations, latest year {newest}, {missing} empty"


def main() -> int:
    failures = 0
    with SessionLocal() as session:
        for job in (bot_bonds, bot_cbr, nbs_inflation, damodaran, damodaran_industry_beta, world_bank):
            try:
                print(job(session))
            except Exception as exc:  # record and continue; /health will show it
                failures += 1
                status(session, job.__name__, False, 24, f"{type(exc).__name__}: {exc}")
                print(f"{job.__name__}: FAILED {exc}")
            session.commit()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
