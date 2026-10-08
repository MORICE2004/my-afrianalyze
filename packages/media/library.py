"""The openly licensed photo library (config/image_library.lock.json, written by pipelines.images).

A photo is chosen by a stated rule, never by guessing what a story is about:
  * a news story from an institution with a photo of its own building gets that photo;
  * otherwise a photo of the city of the first country the story is about;
  * a company gets a photo only if the library has one of that company.
Every photo carries its caption, author, licence and source page, and is marked kind="library" so pages can say
it shows the institution or the city, not the event.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from packages.core.config import settings

# The same allow-list pipelines.images enforces before downloading.
ALLOWED_LICENCE = re.compile(r"^(CC0|Public domain|CC BY(-SA)? \d\.\d( [a-z]{2})?)$", re.I)


@lru_cache(maxsize=1)
def _lock() -> dict:
    path = settings.CONFIG_DIR / "image_library.lock.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _public(entry: dict) -> dict:
    return {"kind": "library", "url": entry["file"], "width": entry["width"], "height": entry["height"],
            "caption": entry["caption"], "author": entry["author"], "licence": entry["licence"],
            "licence_url": entry.get("licence_url"), "source_page": entry["commons_page"], "source": "Wikimedia Commons"}


def _find(key: str, value: str) -> dict | None:
    for e in _lock().values():
        if value in (e.get("for") or {}).get(key, []):
            return _public(e)
    return None


def _all(key: str, value: str) -> list[dict]:
    return [_public(e) for e in _lock().values() if value in (e.get("for") or {}).get(key, [])]


def for_news(source_id: str, countries: list[str]) -> list[dict]:
    """Suitable photos in order of preference: the publishing institution's, then each country's city. A page
    shows the first one it has not already used, so a photo is not repeated down the page."""
    out = _all("news_source", source_id)
    for c in countries:
        out += _all("country", c)
    return out




def for_security(security_id: str) -> dict | None:
    return _find("security", security_id)
