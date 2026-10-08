r"""Download the openly licensed photo library (config/image_library.json) from Wikimedia Commons.

    .venv\Scripts\python -m pipelines.images             # new files only
    .venv\Scripts\python -m pipelines.images --refresh   # re-check every licence and file

For each file: ask the Commons API for its licence, author and a 1600-pixel rendering; refuse it unless the
licence is CC0, public domain, CC BY or CC BY-SA; save the rendering under apps/web/public/media/library/<id>.jpg
(the site serves its own copy, so no visitor request goes to Commons); and record what was checked in
config/image_library.lock.json. Requests are spaced out and identify AfriEdge, per Wikimedia's API etiquette.
A file that fails keeps its previous lock entry, so a temporary error never removes a photo already in use.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import sys
import time
from datetime import datetime, timezone

import requests

from packages.core.config import REPO_ROOT, settings

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "AfriEdge/1.0 (photo library for an investment research site; repository MORICE2004/my-afrianalyze)"}
OUT = REPO_ROOT / "apps/web/public/media/library"
LOCK = settings.CONFIG_DIR / "image_library.lock.json"
ALLOWED = re.compile(r"^(CC0|Public domain|CC BY(-SA)? \d\.\d( [a-z]{2})?)$", re.I)
MIN_WIDTH = 900


def text(meta: dict, key: str) -> str:
    raw = meta.get(key, {}).get("value", "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(str(raw)))).strip()


def licence_ok(name: str) -> bool:
    return bool(ALLOWED.match(name.strip()))


def lookup(title: str) -> dict:
    for attempt in range(4):
        r = requests.get(API, headers=UA, timeout=30, params={
            "action": "query", "format": "json", "titles": title, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1600})
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        page = next(iter(r.json()["query"]["pages"].values()))
        if "imageinfo" not in page:
            raise ValueError(f"{title} not found on Commons")
        return page
    raise RuntimeError("Commons kept asking us to slow down (HTTP 429)")


def to_jpeg(content: bytes) -> tuple[bytes, int, int]:
    from PIL import Image

    with Image.open(io.BytesIO(content)) as im:
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
        return buf.getvalue(), im.width, im.height


def main() -> int:
    cfg = json.loads((settings.CONFIG_DIR / "image_library.json").read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)
    failures = 0
    refresh = "--refresh" in sys.argv
    for item in cfg["images"]:
        if not refresh and item["id"] in lock and (OUT / f"{item['id']}.jpg").exists():
            continue  # already checked and stored; --refresh re-checks every licence
        try:
            page = lookup(item["commons"])
            info = page["imageinfo"][0]
            meta = info.get("extmetadata", {})
            licence = text(meta, "LicenseShortName")
            if not licence_ok(licence):
                raise ValueError(f"licence {licence!r} is not on the allowed list")
            if info["width"] < MIN_WIDTH:
                raise ValueError(f"only {info['width']} px wide")
            time.sleep(1.5)
            img = requests.get(info.get("thumburl") or info["url"], headers=UA, timeout=60)
            img.raise_for_status()
            data, w, h = to_jpeg(img.content)
            (OUT / f"{item['id']}.jpg").write_bytes(data)
            lock[item["id"]] = {
                "file": f"/media/library/{item['id']}.jpg", "width": w, "height": h, "caption": item["caption"],
                "for": item["for"], "commons_title": item["commons"], "commons_page": info["descriptionurl"],
                "author": text(meta, "Artist") or "Unknown", "licence": licence,
                "licence_url": text(meta, "LicenseUrl") or None, "description": text(meta, "ImageDescription")[:300],
                "taken": text(meta, "DateTimeOriginal")[:20] or None,
                "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sha256": hashlib.sha256(data).hexdigest()}
            print(f"{item['id']}: {licence}, {w}x{h}, {lock[item['id']]['author'][:40]}")
        except Exception as exc:  # keep any earlier copy; report and continue
            failures += 1
            print(f"{item['id']}: NOT UPDATED ({type(exc).__name__}: {exc})", file=sys.stderr)
        time.sleep(2)
    LOCK.write_text(json.dumps(lock, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
