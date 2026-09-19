r"""Download a bank's annual reports and record provenance.

Usage (PowerShell, from the repo root):
    .venv\Scripts\python -m pipelines.banks.download_reports --bank=crdb

Writes PDFs to data/raw/<bank>/ and a manifest (URL, retrieval time, SHA-256,
size) to data/raw/<bank>/manifest.json. A file whose hash changes between runs
is reported, never silently replaced.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from pipelines.banks.profiles import profile_for


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    profile = profile_for(next((a.split("=", 1)[1] for a in argv if a.startswith("--bank=")), ""))
    if profile is None:
        print("Usage: python -m pipelines.banks.download_reports --bank=<nmb|crdb>")
        return 2
    headers = {
        # Some download endpoints return 403 without a browser user agent and referer.
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36",
        "Referer": profile.listing_url,
    }
    raw_dir = profile.raw_dir
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    failures = 0
    for year, url in sorted(profile.reports.items()):
        target = profile.pdf_path(year)
        resp = requests.get(url, headers=headers, timeout=600)
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
            target = raw_dir / f"{target.stem}_{new_hash[:12]}.pdf"
        tmp.replace(target)
        manifest[str(year)] = {
            "fiscal_year": year,
            "file": target.as_posix(),
            "url": url,
            "listing_url": profile.listing_url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sha256": new_hash,
            "bytes": target.stat().st_size,
        }
        print(f"OK   {year}: {target} {target.stat().st_size:,} bytes sha256={new_hash[:16]}")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
