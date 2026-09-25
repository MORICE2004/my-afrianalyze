"""Check every source in the directive's list: can it be reached, what do its robots rules say, does it put a
bot challenge in front, and does one real data request return data we can parse?

Reachable is not the same as implemented. The result says only what this probe proved; docs/DATA_SOURCE_MATRIX.md
records which sources also have a working loader. Run: .venv\\Scripts\\python -m pipelines.probe_sources
It makes about two requests per source, one second apart, and writes nothing to the database.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

UA = "MyAfriAnalyzeResearchBot/0.1 (source availability check; contact via github.com/MORICE2004/my-afrianalyze)"

# (key, country, home page, a data request, what a real answer must contain)
SOURCES = [
    ("DSE prices", "TZ", "https://dse.co.tz/",
     "https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=NMB&days=5&class=EQUITY",
     '"closing_price"'),
    ("CMSA", "TZ", "https://www.cmsa.go.tz/", None, None),
    ("Bank of Tanzania", "TZ", "https://www.bot.go.tz/", None, None),
    ("NBS Tanzania", "TZ", "https://www.nbs.go.tz/", None, None),
    ("NSE Kenya", "KE", "https://www.nse.co.ke/", None, None),
    ("CMA Kenya", "KE", "https://www.cma.or.ke/", None, None),
    ("CMA Resource Centre", "KE", "https://www.cmarcp.or.ke/", None, None),
    ("Central Bank of Kenya", "KE", "https://www.centralbank.go.ke/", None, None),
    ("KNBS", "KE", "https://www.knbs.or.ke/", None, None),
    ("USE Uganda", "UG", "https://www.use.or.ug/", None, None),
    ("Bank of Uganda", "UG", "https://www.bou.or.ug/", None, None),
    ("UBOS", "UG", "https://www.ubos.org/", None, None),
    ("World Bank API", "GLOBAL", "https://data.worldbank.org/",
     "https://api.worldbank.org/v2/country/TZA/indicator/NY.GDP.MKTP.CD?format=json&per_page=3",
     '"NY.GDP.MKTP.CD"'),
    # The country in the path is ignored: the answer holds every country, so look for Tanzania's key.
    ("IMF DataMapper API", "GLOBAL", "https://www.imf.org/",
     "https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/TZA", '"TZA":{'),
    ("ECB Data API", "GLOBAL", "https://data.ecb.europa.eu/",
     "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1&format=jsondata",
     '"observations"'),
    ("UN Comtrade (public preview)", "GLOBAL", "https://comtradeplus.un.org/",
     "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=834&period=2023&partnerCode=0"
     "&cmdCode=TOTAL&flowCode=X", '"primaryValue"'),
]

CHALLENGE_MARKERS = ("just a moment", "cf-chl", "attention required", "captcha", "access denied")


def _get(url: str) -> tuple[int | None, str, dict]:
    """One retry, because a single timeout says little about a source. Certificate errors are reported,
    never bypassed (KNBS and UBOS fail verification as of 2026-09-25)."""
    for attempt in (1, 2):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=40)
            return r.status_code, r.text, dict(r.headers)
        except requests.exceptions.SSLError:
            return None, "SSLError: certificate fails verification", {}
        except requests.RequestException as exc:
            if attempt == 2:
                return None, type(exc).__name__, {}
            time.sleep(3)


def probe(key: str, country: str, home: str, data_url: str | None, marker: str | None) -> dict:
    out = {"source": key, "country": country, "home": home}
    host = f"{urlparse(home).scheme}://{urlparse(home).netloc}"
    code, body, _ = _get(host + "/robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    if code == 200 and "user-agent" in body.lower():
        rp.parse(body.splitlines())
        out["robots"] = "present"
        out["robots_allows_home"] = rp.can_fetch(UA, home)
        if data_url:
            out["robots_allows_data"] = rp.can_fetch(UA, data_url)
    else:
        out["robots"] = f"none ({code})"
    time.sleep(1)
    code, body, headers = _get(home)
    out["home_status"] = code
    if code is None:
        out["error"] = body
    challenged = code in (403, 429, 503) and (
        "cf-mitigated" in {h.lower() for h in headers} or any(m in body[:20000].lower() for m in CHALLENGE_MARKERS))
    out["bot_challenge"] = challenged
    if data_url:
        time.sleep(1)
        dcode, dbody, _ = _get(data_url)
        out["data_status"] = dcode
        out["data_parsed"] = bool(dcode == 200 and marker and marker in dbody)
    if data_url and out["data_parsed"] and out.get("robots_allows_data", True):
        out["result"] = "WORKING"
    elif code is None:
        out["result"] = "UNAVAILABLE"
    elif challenged:
        out["result"] = "BLOCKED"
    elif code == 200:
        out["result"] = "REACHABLE_NO_LOADER"
    else:
        out["result"] = "UNAVAILABLE"
    return out


def main() -> int:
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = [probe(*s) for s in SOURCES]
    print(json.dumps({"checked_at": checked_at, "user_agent": UA, "results": results}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
