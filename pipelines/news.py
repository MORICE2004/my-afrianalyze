r"""Fetch economic and market news from the whitelisted sources into the news_items cache.

    .venv\Scripts\python -m pipelines.news            # all CONNECTED sources
    .venv\Scripts\python -m pipelines.news cbk bot    # only these

Pages read the cache; they never call a news source. Each source is fetched through the feed or API its
publisher offers (config/news_sources.json), with an honest User-Agent. The raw response is kept under
data/raw/news/ with its SHA-256. A source that fails is recorded in data_source_status and the others still run,
so one outage never empties the page. Stories already cached are updated in place (same canonical URL, same id).

Times: an item dated more than a day in the future is rejected and counted (the World Bank API returns some
scheduled publications with a future launch date); it is not stored with a made-up date.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from defusedxml import ElementTree  # no external entities or entity expansion from a feed

import requests

from packages.core.config import settings
from packages.database.models import DataSourceStatus, NewsItem, Security
from packages.database.session import SessionLocal
from packages.news.classify import EXCHANGE, classify

UA = {"User-Agent": "AfriEdge/1.0 (economic news cache; headlines and links only)"}
RAW = Path("data/raw/news")
MAX_AGE_HOURS = 72  # a source with no successful fetch for three days is shown to admins as stale
EAT = timezone(timedelta(hours=3))


def now() -> datetime:
    return datetime.now(timezone.utc)


def load_sources() -> list[dict]:
    return json.loads((settings.CONFIG_DIR / "news_sources.json").read_text(encoding="utf-8"))["sources"]


def item_id(url: str) -> str:
    return hashlib.sha1(canonical(url).encode()).hexdigest()


def canonical(url: str) -> str:
    """https, no fragment, no tracking query; the World Bank API returns http:// links to https pages."""
    url = url.strip().split("#")[0]
    url = re.sub(r"[?&]utm_[^&]+", "", url)
    return re.sub(r"^http://", "https://", url)


def clean(text: str | None) -> str:
    # U+FFFD: a character the publisher's own page already lost; dropped rather than guessed.
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or "")).replace("�", "")).strip()


# ------------------------------------------------------------------ parsers (pure; tested on stored responses)

def parse_rss(content: bytes) -> list[dict]:
    root = ElementTree.fromstring(content)
    out = []
    for it in root.iter("item"):
        title, link, date = it.findtext("title"), it.findtext("link"), it.findtext("pubDate")
        if not (title and link and date):
            continue
        out.append({"title": clean(title), "url": link, "published_at": parsedate_to_datetime(date),
                    "summary": clean(it.findtext("description"))[:400] or None})
    return out


def parse_bot_press(content: bytes, base: str = "https://www.bot.go.tz") -> list[dict]:
    """The Bank of Tanzania press-release table. Each row links the release PDF, whose file name starts with
    its own timestamp (YYYYMMDDhhmm...). The listed date is month/day/year; the two must agree on the day, so
    the date is never read ambiguously. Rows where they disagree are skipped."""
    page = content.decode("utf-8", errors="ignore")
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        link = re.search(r'href="(/Adverts/PressRelease/[^"]+\.pdf)"', row)
        listed = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", re.sub(r"<[^>]+>", " ", row))
        if not link:
            continue
        stamp = re.search(r"/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})\d*\.pdf$", link.group(1))
        if not stamp:
            continue
        y, mo, d, hh, mi = (int(x) for x in stamp.groups())
        if listed and (int(listed.group(1)), int(listed.group(2)), int(listed.group(3))) != (mo, d, y):
            continue
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        title = max((c for c in cells if not re.fullmatch(r"[\d./ ]*", c)), key=len, default="")
        if not title:
            continue
        out.append({"title": title, "url": base + link.group(1),
                    "published_at": datetime(y, mo, d, hh, mi, tzinfo=EAT), "summary": None})
    return out


def merge_bot_languages(english: list[dict], swahili: list[dict]) -> list[dict]:
    by_time = {it["published_at"]: it for it in swahili}
    out = []
    for it in english:
        if " " not in it["title"].strip() and it["published_at"] in by_time:
            it = {**by_time[it["published_at"]], "url": it["url"], "language": "sw"}
        out.append(it)
    return out


def parse_worldbank(content: bytes) -> list[dict]:
    docs = json.loads(content).get("documents", {})
    out = []
    for key, d in docs.items():
        if key == "facets" or not isinstance(d, dict) or not d.get("url") or not d.get("lnchdt"):
            continue
        title = d.get("title")
        title = title.get("cdata!") if isinstance(title, dict) else title
        descr = d.get("descr")
        descr = descr.get("cdata!") if isinstance(descr, dict) else descr
        if not title:
            continue
        out.append({"title": clean(title), "url": d["url"], "summary": clean(descr)[:400] or None,
                    "published_at": datetime.fromisoformat(d["lnchdt"].replace("Z", "+00:00")),
                    "content_type": d.get("displayconttype")})
    return out


def fetch(source: dict) -> list[tuple[bytes, list[dict]]]:
    """One or more raw responses for a source, each with its parsed items."""
    if source["kind"] == "rss":
        r = requests.get(source["url"], headers=UA, timeout=30)
        r.raise_for_status()
        return [(r.content, parse_rss(r.content))]
    if source["kind"] == "bot_press":
        # The English list links the English release; a few English titles are bare file names, and for those
        # the Swahili title of the same release (same file timestamp) is used instead, marked as Swahili.
        en = requests.get(source["url"], headers=UA, timeout=30, params={"lang": "en"})
        en.raise_for_status()
        sw = requests.get(source["url"], headers=UA, timeout=30)
        sw.raise_for_status()
        return [(en.content + sw.content,
                 merge_bot_languages(parse_bot_press(en.content), parse_bot_press(sw.content)))]
    if source["kind"] == "worldbank_api":
        got = []
        for country in source["countries"]:
            # The API's country and sort parameters do not filter news, so: full-text search for the country,
            # English only, the last 180 days. Each item must still name an East African country to be kept.
            r = requests.get(source["url"], headers=UA, timeout=30, params={
                "format": "json", "rows": 30, "qterm": country, "lang_exact": "English",
                "strdate": (now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                "fl": "title,url,lnchdt,descr,displayconttype"})
            r.raise_for_status()
            got.append((r.content, parse_worldbank(r.content)))
        return got
    raise ValueError(f"no parser for kind {source['kind']!r}")


# ------------------------------------------------------------------ store

def store(session, source: dict, raw: bytes, items: list[dict], securities: list[dict],
          retrieved_at: datetime, seen: set[str] | None = None) -> dict:
    seen = set() if seen is None else seen
    sha = hashlib.sha256(raw).hexdigest()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{source['id']}-{retrieved_at:%Y%m%dT%H%M%S}-{sha[:12]}.raw").write_bytes(raw)
    counts = {"stored": 0, "updated": 0, "future_dated": 0, "not_regional": 0}
    horizon = retrieved_at + timedelta(days=1)
    for it in items:
        published = it["published_at"]
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published > horizon:
            counts["future_dated"] += 1
            continue
        if not it["url"].startswith(("http://", "https://")):
            continue
        tag = classify(it["title"], source_country=source.get("country"),
                       summary=it.get("summary") if source.get("summary_allowed") else None,
                       securities=securities)
        if not tag.countries:  # a multi-country publisher's story that names no East African country
            counts["not_regional"] += 1
            continue
        nid = item_id(it["url"])
        if nid in seen:
            continue
        seen.add(nid)
        row = session.get(NewsItem, nid)
        counts["updated" if row else "stored"] += 1
        row = row or NewsItem(id=nid)
        row.source_id, row.title, row.url = source["id"], it["title"], canonical(it["url"])
        row.language = it.get("language") or source.get("language", "en")
        row.published_at, row.retrieved_at = published, retrieved_at
        row.summary = it.get("summary") if source.get("summary_allowed") else None
        row.countries, row.categories = tag.countries, tag.categories
        row.relevance, row.relevance_reason, row.related = tag.relevance, tag.relevance_reason, tag.related
        row.raw_sha256 = sha
        session.merge(row)
    return counts


def record(session, key: str, ok: bool, detail: str) -> None:
    row = session.get(DataSourceStatus, key) or DataSourceStatus(source=key)
    row.last_attempt_at = now()
    if ok:
        row.last_success_at = row.last_attempt_at
    row.status = "ok" if ok else "failed"
    row.max_age_hours = MAX_AGE_HOURS
    row.detail = detail
    session.merge(row)


def security_dicts(session) -> list[dict]:
    return [{"id": s.id, "name": s.name, "ticker": s.local_ticker, "exchange": s.exchange, "sector": s.sector,
             "country_code": {v: k for k, v in EXCHANGE.items()}.get(s.exchange)}
            for s in session.query(Security).all() if s.id != "DSE:DSEI"]


def main(argv: list[str]) -> int:
    wanted = set(argv)
    failures = 0
    with SessionLocal() as session:
        securities = security_dicts(session)
        for source in load_sources():
            if source["state"] != "CONNECTED" or (wanted and source["id"] not in wanted):
                continue
            try:
                total = {"stored": 0, "updated": 0, "future_dated": 0, "not_regional": 0}
                seen: set[str] = set()
                for raw, items in fetch(source):
                    for k, v in store(session, source, raw, items, securities, now(), seen).items():
                        total[k] += v
                detail = (f"{total['stored']} new, {total['updated']} refreshed"
                          + (f", {total['future_dated']} future-dated items rejected" if total["future_dated"] else "")
                          + (f", {total['not_regional']} outside East Africa skipped" if total["not_regional"] else ""))
                record(session, source["status_key"], True, detail)
                print(f"{source['id']}: {detail}")
            except Exception as exc:  # one source failing must not stop the others
                failures += 1
                record(session, source["status_key"], False, f"{type(exc).__name__}: {str(exc)[:200]}")
                print(f"{source['id']}: FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
            session.commit()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
