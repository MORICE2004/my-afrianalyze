"""Share splits. NMB split 1:10 on 2026-08-24, which is the one event that can silently wreck
every per-share number in the product, so it gets its own tests.

Without the adjustment, the DSE's published series falls from TZS 17,700 to TZS 1,850 in a day and
FY2025 earnings per share stay on the old 500,000,000 shares. That combination gave a price/earnings
ratio of 1.4 and a price/book of 0.33 for a bank earning about 30% on equity, which any valuation
would have read as "deeply undervalued".
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal as D

import pytest

from packages.analysis import corporate_actions as ca
from packages.analysis.bank_ratios import add_derived
from packages.analysis.bank_valuation import base_year_structure
from packages.database.models import FinancialFact
from packages.database.session import SessionLocal

SPLIT = date(2026, 8, 24)


def test_the_nmb_split_is_recorded_with_its_source():
    actions = ca.load_actions("DSE:NMB")
    assert len(actions) == 1
    a = actions[0]
    assert a["ratio_new_for_old"] == 10 and a["effective_date"] == "2026-08-24"
    assert len(a["evidence"]) >= 2, "a corporate action must cite more than the price series itself"
    assert any("dse" in e.lower() or "17,700" in e for e in a["evidence"])


def test_crdb_has_no_split_recorded():
    assert ca.load_actions("DSE:CRDB") == []


def test_an_action_without_evidence_is_refused(tmp_path):
    bad = tmp_path / "actions.json"
    bad.write_text(json.dumps({"actions": [
        {"security_id": "DSE:X", "kind": "share_split", "ratio_new_for_old": 2,
         "effective_date": "2026-01-01", "evidence": []}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="cites no source"):
        ca.load_actions("DSE:X", bad)


def test_prices_before_the_split_are_divided_and_prices_after_are_left_alone():
    actions = ca.load_actions("DSE:NMB")
    raw = {date(2026, 8, 19): D("17700"), date(2026, 8, 24): D("1850"), date(2026, 9, 18): D("2070")}
    adj = ca.adjust_prices(raw, actions)
    assert adj[date(2026, 8, 19)] == D("1770")     # 17,700 / 10
    assert adj[date(2026, 8, 24)] == D("1850")     # on or after the effective date: untouched
    assert adj[date(2026, 9, 18)] == D("2070")


def test_the_split_no_longer_looks_like_a_ninety_per_cent_fall():
    actions = ca.load_actions("DSE:NMB")
    adj = ca.adjust_prices({date(2026, 8, 19): D("17700"), date(2026, 8, 24): D("1850")}, actions)
    move = adj[SPLIT] / adj[date(2026, 8, 19)] - 1
    assert abs(move) < D("0.06"), f"a split must not read as a return; got {move:.1%}"


def test_per_share_factor_is_ten_before_the_split_and_one_after():
    actions = ca.load_actions("DSE:NMB")
    assert ca.per_share_factor(actions, date(2025, 12, 31)) == 10   # the FY2025 accounts
    assert ca.per_share_factor(actions, date(2026, 8, 19)) == 10
    assert ca.per_share_factor(actions, SPLIT) == 1
    assert ca.per_share_factor([], date(2025, 12, 31)) == 1


def test_no_split_leaves_a_series_exactly_as_published():
    raw = {date(2026, 8, 19): D("2920"), date(2026, 9, 18): D("2810")}
    assert ca.adjust_prices(raw, []) == raw


# --------------------------------------------------------- the effect on the valuation

def _facts(security_id: str) -> dict:
    with SessionLocal() as s:
        rows = s.query(FinancialFact).filter_by(security_id=security_id, is_primary=True).all()
    facts: dict = {}
    for f in rows:
        facts.setdefault(f.item_code, {})[f.fiscal_year] = f.value
    add_derived(facts)          # the valuation needs the derived lines too
    return facts


def test_the_share_count_used_for_value_per_share_is_todays_count():
    """FY2025 profit / EPS gives the old 500,000,000. Today there are 5,000,000,000 shares."""
    facts = _facts("DSE:NMB")
    if "eps" not in facts:
        pytest.skip("NMB data not loaded")
    before = base_year_structure(facts, 2025)
    after = base_year_structure(facts, 2025, ca.per_share_factor(ca.load_actions("DSE:NMB"),
                                                                 date(2025, 12, 31)))
    assert before["shares"] == D("500000000")
    assert after["shares"] == D("5000000000")
    # The whole bank is worth the same either way: only the slicing changed.
    assert before["book_value"] == after["book_value"]


def test_the_multiples_are_believable_once_the_split_is_applied():
    """A guard against the failure this file exists for: price and earnings on different bases."""
    facts = _facts("DSE:NMB")
    if "eps" not in facts:
        pytest.skip("NMB data not loaded")
    factor = ca.per_share_factor(ca.load_actions("DSE:NMB"), date(2025, 12, 31))
    st = base_year_structure(facts, 2025, factor)
    price = D("2070")                                   # close on 2026-09-18, post-split
    pe = price / (facts["eps"][2025] / factor)
    pb = price / (st["book_value"] * D(10 ** 6) / st["shares"])
    assert D("5") < pe < D("30"), f"price/earnings {pe:.1f} is not a believable bank multiple"
    assert D("0.5") < pb < D("6"), f"price/book {pb:.2f} is not a believable bank multiple"
