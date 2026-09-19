"""The rule-based notes must never contradict the direction of the numbers they quote."""
from decimal import Decimal as D

from packages.analysis.notes import line_note


def test_charge_that_fell_while_loans_grew():
    facts = {"impairment_loans": {2024: D("-85100"), 2025: D("-80600")},
             "gross_loans": {2024: D("8739221"), 2025: D("10688021")}}
    note = line_note(facts, "impairment_loans", "Impairment charge on loans", 2025)["text"]
    assert "fell 5.3%" in note
    assert "fell while gross loans grew" in note
    assert "lower relative to the loan book" in note
    assert "grew more slowly" not in note and "rising" not in note


def test_both_growing():
    facts = {"deposits_customers": {2024: D("100"), 2025: D("130")}, "total_assets": {2024: D("100"), 2025: D("120")}}
    note = line_note(facts, "deposits_customers", "Deposits", 2025)
    assert "rose 30.0%" in note["text"] and "grew faster than total assets" in note["text"]
    assert note["numbers"] == [D("30.0"), D("0.1"), 2025, D("20.0")]


def test_both_falling():
    facts = {"loans_advances_net": {2024: D("100"), 2025: D("90")},
             "deposits_customers": {2024: D("100"), 2025: D("80")}}
    note = line_note(facts, "loans_advances_net", "Net loans", 2025)["text"]
    assert "net loans fell less than customer deposits" in note


def test_no_prior_year_no_note():
    assert line_note({"total_assets": {2025: D("1")}}, "total_assets", "Total assets", 2025) is None
