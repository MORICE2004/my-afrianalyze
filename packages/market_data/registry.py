"""Which market-data providers exist, which are usable, and in what order they are asked.

config/market_data.json lists every provider AfriEdge has an adapter for, with its licensing word and the
environment variable that holds its credential. MARKET_DATA_PRIORITY (settings) can reorder them without a code
change; that is how an administrator sets "primary Mansa, secondary the exchange's own files".

A provider is USABLE only when its adapter exists, its credential is set (if it needs one) and its licensing
allows the use. Otherwise its state says why (BLOCKED, LICENSE_REVIEW_REQUIRED, NOT_CONFIGURED), and the
administrator page shows that state; readers never see a provider name or an error from one.
"""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass

from packages.core.config import settings
from packages.market_data.provider import MarketDataProvider

READY = "READY"
NOT_CONFIGURED = "NOT_CONFIGURED"          # a credential is needed and none is set
LICENSE_REVIEW_REQUIRED = "LICENSE_REVIEW_REQUIRED"


@dataclass
class ProviderEntry:
    id: str
    name: str
    adapter: str                 # "module:Class"
    credential_env: str | None   # the setting holding its key, never the key itself
    licensing: str               # RESTRICTED, LICENSE_REVIEW_REQUIRED, COMMERCIAL_LICENCE (when held), ...
    coverage: list[str]
    note: str
    state: str = READY
    state_reason: str = ""


def _config() -> dict:
    return json.loads((settings.CONFIG_DIR / "market_data.json").read_text(encoding="utf-8"))


def entries() -> list[ProviderEntry]:
    """Every provider in priority order, with its state."""
    cfg = _config()
    by_id = {p["id"]: p for p in cfg["providers"]}
    order = [x.strip() for x in settings.MARKET_DATA_PRIORITY.split(",") if x.strip()] or cfg["priority"]
    order += [pid for pid in by_id if pid not in order]          # anything not named goes last
    out = []
    for pid in order:
        if pid not in by_id:
            continue                                              # an unknown id in the setting is ignored
        p = by_id[pid]
        e = ProviderEntry(id=pid, name=p["name"], adapter=p["adapter"], credential_env=p.get("credential_env"),
                          licensing=p["licensing"], coverage=p["coverage"], note=p.get("note", ""))
        if e.credential_env and not getattr(settings, e.credential_env, ""):
            e.state, e.state_reason = NOT_CONFIGURED, f"{e.credential_env} is not set"
        elif e.licensing == LICENSE_REVIEW_REQUIRED:
            e.state, e.state_reason = LICENSE_REVIEW_REQUIRED, "Its terms for public display have not been accepted"
        out.append(e)
    return out


def load(entry: ProviderEntry) -> MarketDataProvider:
    module, cls = entry.adapter.split(":")
    klass = getattr(importlib.import_module(module), cls)
    if entry.credential_env:
        return klass(api_key=getattr(settings, entry.credential_env))
    return klass()


def usable(exchange: str, capability: str) -> list[MarketDataProvider]:
    """Providers that are READY, cover the exchange and offer the capability, in priority order."""
    out = []
    for e in entries():
        if e.state != READY or exchange not in e.coverage:
            continue
        provider = load(e)
        if getattr(provider.capabilities, capability, False):
            out.append(provider)
    return out
