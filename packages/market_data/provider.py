"""The market-data provider interface. Every source of prices is an adapter behind it.

Where providers sit in AfriEdge:

    provider adapter (DSE public files, Mansa, EODHD, later LSEG or Bloomberg)
        -> pipelines (refresh, reconcile): raw answer stored with its SHA-256, then MERGED into price_bars
        -> the database, the only thing the API reads
        -> the web app, which never calls a provider

So switching or adding a provider is configuration (config/market_data.json, MARKET_DATA_PRIORITY), never a
change to a page. Each stored bar keeps the document it came from (SourceDocument.publisher names the provider),
so the source used is always recorded with the data.

The interface is split by capability, because no provider offers everything: the DSE's public endpoints have
history and quotes but no symbol search; a provider without index data simply does not implement it. An adapter
says what it can do in `capabilities`; asking it for something else raises ProviderUnavailable.

Nothing here returns a default or an estimate. A provider that cannot answer raises ProviderUnavailable with a
public message (shown to readers) and a technical detail (shown to administrators only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

# What a quote's timing means. LIVE is deliberately absent: nothing AfriEdge shows is a live price.
CURRENT = "CURRENT"          # the close of the latest completed session
DELAYED = "DELAYED"          # an intraday price published with a delay (e.g. about 30 minutes)
STALE = "STALE"              # older than the source's freshness limit


class ProviderUnavailable(Exception):
    """The provider could not answer. `public` is safe to show anyone; `detail` is for administrators."""

    def __init__(self, provider: str, public: str, detail: str = ""):
        super().__init__(f"{provider}: {detail or public}")
        self.provider, self.public, self.detail = provider, public, detail


@dataclass(frozen=True)
class Bar:
    """One day as the provider published it. Optional fields stay None when the provider does not state them."""
    trade_date: date
    close: Decimal
    volume: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    turnover: Decimal | None = None
    market_cap: Decimal | None = None

    def activity(self) -> dict:
        return {"open": self.open, "high": self.high, "low": self.low, "turnover": self.turnover,
                "market_cap": self.market_cap}


@dataclass(frozen=True)
class Quote:
    symbol: str                  # the provider's own code for the instrument
    price: Decimal
    currency: str
    as_of: datetime | date       # the provider's timestamp, never the time we asked
    timing: str                  # CURRENT, DELAYED or STALE
    previous_close: Decimal | None = None
    volume: Decimal | None = None


@dataclass(frozen=True)
class RawAnswer:
    """What came back over the wire, kept so the stored file and its SHA-256 are exactly what was received."""
    url: str                     # the address asked, WITHOUT any credential
    content: bytes
    retrieved_at: datetime


@dataclass(frozen=True)
class History:
    bars: list[Bar]
    raw: RawAnswer
    currency: str


@dataclass(frozen=True)
class ProviderSecurity:
    symbol: str                  # the provider's code
    name: str
    exchange: str
    currency: str
    isin: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class MarketStatus:
    exchange: str
    state: str                   # OPEN, CLOSED or UNKNOWN; never guessed from a clock alone
    as_of: datetime
    detail: str = ""


@dataclass
class Capabilities:
    quote: bool = False
    history: bool = False
    index: bool = False
    search: bool = False
    exchanges: bool = False
    market_status: bool = False
    corporate_actions: bool = False
    exchanges_covered: list[str] = field(default_factory=list)   # e.g. ["DSE"]
    timing: str = CURRENT        # what its latest price is: CURRENT (end of day) or DELAYED (intraday)


@runtime_checkable
class QuoteProvider(Protocol):
    def latest_quote(self, symbol: str) -> Quote: ...


@runtime_checkable
class HistoricalDataProvider(Protocol):
    def history(self, symbol: str, days: int) -> History: ...


@runtime_checkable
class IndexDataProvider(Protocol):
    def index_history(self, code: str, days: int) -> History: ...


@runtime_checkable
class SecurityMasterProvider(Protocol):
    def search(self, query: str) -> list[ProviderSecurity]: ...

    def exchanges(self) -> list[dict]: ...


@runtime_checkable
class CorporateActionsProvider(Protocol):
    def corporate_actions(self, symbol: str) -> list[dict]: ...


class MarketDataProvider:
    """Base for adapters. Subclasses set `id`, `name`, `capabilities` and implement what they support."""

    id: str = ""
    name: str = ""
    capabilities: Capabilities = Capabilities()

    def symbol_for(self, instrument_id: str) -> str:
        """The provider's code for an AfriEdge instrument id (DSE:NMB). Overridden where codes differ."""
        return instrument_id.split(":", 1)[1]

    def _refuse(self, what: str) -> ProviderUnavailable:
        return ProviderUnavailable(self.id, "This information is not available from the configured data source.",
                                   f"{self.name} does not provide {what}")

    def latest_quote(self, symbol: str) -> Quote:
        raise self._refuse("quotes")

    def history(self, symbol: str, days: int) -> History:
        raise self._refuse("price history")

    def index_history(self, code: str, days: int) -> History:
        raise self._refuse("index data")

    def search(self, query: str) -> list[ProviderSecurity]:
        raise self._refuse("security search")

    def exchanges(self) -> list[dict]:
        raise self._refuse("exchange metadata")

    def market_status(self, exchange: str) -> MarketStatus:
        raise self._refuse("market status")

    def corporate_actions(self, symbol: str) -> list[dict]:
        raise self._refuse("corporate actions")
