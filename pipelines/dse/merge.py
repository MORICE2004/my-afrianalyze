"""Merge downloaded daily bars into the stored series without ever losing history.

Both DSE importers used to delete every stored bar of an instrument and insert the download. That is safe
only when the download covers the whole history; a scheduled refresh that fetches the last few days would
have erased ten years. This merge is the only way bars are written now:

- a day not stored yet is inserted, with the new file as its source;
- a day stored with the same close and volume is left alone, and keeps its original source document;
- a day stored with a DIFFERENT close is a revision by the source. The stored close is kept and the
  revision is reported, because a past price silently changing under a valuation is worse than a stale
  one. `accept_revisions=True` (the importers' --accept-revisions) applies them, after a person has looked;
- a volume-only difference is applied (volume is not used in any valuation) and counted;
- a stored day missing from the download is kept. Nothing is ever deleted here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from packages.database.models import PriceBar

Bar = tuple[Decimal, Decimal | None]          # (close, volume)


@dataclass
class MergeResult:
    inserted: int = 0
    unchanged: int = 0
    volume_updated: int = 0
    revisions: list[tuple[date, Decimal, Decimal]] = field(default_factory=list)   # (day, stored, new)
    revisions_applied: bool = False
    preserved: int = 0                         # stored days the download did not include

    def summary(self) -> str:
        parts = [f"{self.inserted} new", f"{self.unchanged} unchanged"]
        if self.volume_updated:
            parts.append(f"{self.volume_updated} volume corrections")
        if self.revisions:
            verb = "applied" if self.revisions_applied else "NOT applied (stored close kept)"
            parts.append(f"{len(self.revisions)} past closes revised by the source, {verb}")
        parts.append(f"{self.preserved} stored days outside the download kept")
        return ", ".join(parts)


def stored_bars(session: Session, instrument: str) -> dict[date, Bar]:
    return {b.trade_date: (b.close, b.volume)
            for b in session.query(PriceBar).filter_by(instrument_id=instrument)}


def merge_bars(session: Session, instrument: str, new: dict[date, Bar], source_document_id: int,
               accept_revisions: bool = False) -> MergeResult:
    existing = {b.trade_date: b for b in session.query(PriceBar).filter_by(instrument_id=instrument)}
    res = MergeResult(revisions_applied=accept_revisions)
    for day, (close, volume) in sorted(new.items()):
        bar = existing.get(day)
        if bar is None:
            session.add(PriceBar(instrument_id=instrument, trade_date=day, close=close, volume=volume,
                                 source_document_id=source_document_id))
            res.inserted += 1
            continue
        if bar.close != close:
            res.revisions.append((day, bar.close, close))
            if accept_revisions:
                bar.close, bar.volume, bar.source_document_id = close, volume, source_document_id
            continue
        if bar.volume != volume and volume is not None:
            bar.volume, bar.source_document_id = volume, source_document_id
            res.volume_updated += 1
            continue
        res.unchanged += 1
    res.preserved = len(set(existing) - set(new))
    return res
