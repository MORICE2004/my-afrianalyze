r"""Download NMB annual reports and record provenance.

Usage (PowerShell, from the repo root):
    .venv\Scripts\python -m pipelines.nmb.download_reports

Writes PDFs to data/raw/nmb/ and a manifest (URL, retrieval time, SHA-256,
size) to data/raw/nmb/manifest.json. A file whose hash changes between runs
is reported, never silently replaced.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from pipelines.nmb.sources import ANNUAL_REPORTS, IR_LISTING_URL

RAW_DIR = Path("data/raw/nmb")
MANIFEST = RAW_DIR / "manifest.json"
HEADERS = {
    # The download endpoint returns 403 without a browser user agent and referer.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    "Referer": IR_LISTING_URL,
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    failures = 0
    for year, url in sorted(ANNUAL_REPORTS.items()):
        target = RAW_DIR / f"NMB_Annual_Report_{year}.pdf"
        resp = requests.get(url, headers=HEADERS, timeout=300)
        if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
            print(f"FAIL {year}: HTTP {resp.status_code}, content-type {resp.headers.get('content-type')}")
            failures += 1
            continue
        tmp = target.with_suffix(".part")
        tmp.write_bytes(resp.content)
        new_hash = sha256_of(tmp)
        old = manifest.get(str(year))
        if old and old["sha256"] != new_hash:
            print(f"WARNING {year}: document changed since last retrieval "
                  f"({old['sha256'][:12]} -> {new_hash[:12]}). Keeping both.")
            target = RAW_DIR / f"NMB_Annual_Report_{year}_{new_hash[:12]}.pdf"
        tmp.replace(target)
        manifest[str(year)] = {
            "fiscal_year": year,
            "file": target.as_posix(),
            "url": url,
            "listing_url": IR_LISTING_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sha256": new_hash,
            "bytes": target.stat().st_size,
        }
        print(f"OK   {year}: {target} {target.stat().st_size:,} bytes sha256={new_hash[:16]}")
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
