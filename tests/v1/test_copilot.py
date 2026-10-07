"""Research copilot: grounding is enforced in code, and every provider failure is AI_UNAVAILABLE.

No real AI provider is called (none is configured on this machine): a fake client returns canned responses,
so these tests prove the request we send and what we do with any answer, not the model's quality.
Synthetic report data."""
from __future__ import annotations

import json
from decimal import Decimal
from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from packages.copilot import assistant
from packages.copilot.context import build_context

REPORT = {
    "security": {"id": "DSE:TEST", "name": "Test Bank Plc", "sector": "Banking", "currency": "TZS"},
    "data_as_of": {"fiscal_year_end": "2025-12-31", "latest_report": "Test AR 2025", "published_on": "2026-03-31"},
    "review": {"run_id": "RA-20261007-001", "status": "draft"},
    "header": {"price": {"available": True, "value": "2040", "trade_date": "2026-10-06",
                         "source": {"title": "DSE prices", "page": None}},
               "recommendation": {"available": True, "model_view": "Inconclusive",
                                  "inconclusive_reason": "views differ by method", "expected_total_return": "0.28"}},
    "statements": [{"code": "IS", "rows": [{"item_code": "net_interest_income", "label": "Net interest income",
                                            "unit": "TZS_millions", "cells": {
        "2025": {"available": True, "value": "1191080", "source": {"title": "Test AR 2025", "page": 150}},
        "2024": {"available": True, "value": "1058407", "source": {"title": "Test AR 2024", "page": 140}}}}]}],
    "ratios": [{"code": "roe", "label": "Return on equity", "values": {
        "2025": {"available": True, "value": "0.2686198627781666", "formula": "profit / average equity"},
        "2024": {"available": False, "reason": "equity for FY2023 not extracted"}}}],
    "cost_of_equity": {"inputs": {}, "result": {"available": True, "value": "0.1293864", "formula": "rf + beta x ERP",
                                                "steps": []}, "alternatives": []},
    "valuation": {"result": {"available": True, "fair_value": "2354.070325", "target_price_12m": "2596.60",
                             "fair_value_range": {"low": "1439.01", "high": "3117.03"}}, "sensitivity": {"rows": []}},
    "technical": {"indicators": {"vwap": {"available": False, "reason": "needs turnover"}}},
    "risks": [{"id": 1, "category": "credit", "title": "Credit risk", "quote": "Loan quality may weaken.",
               "source": {"title": "Test AR 2025", "page": 107}}],
    "gaps": ["Model view: views differ by method"],
}


class FakeClient:
    def __init__(self, payload=None, stop="end_turn", raises=None):
        self.payload, self.stop, self.raises, self.sent = payload, stop, raises, None
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.sent = kwargs
        if self.raises:
            raise self.raises
        text = self.payload if isinstance(self.payload, str) else json.dumps(self.payload)
        return SimpleNamespace(stop_reason=self.stop, model="claude-opus-5-5",
                               content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=100, output_tokens=50, cache_read_input_tokens=90))


def _answer(facts=(), calc=(), interp=(), answerable=True, unavailable=()):
    st = lambda items: [{"text": t, "keys": k} for t, k in items]  # noqa: E731
    return {"answerable": answerable, "source_facts": st(facts), "calculated_results": st(calc),
            "interpretation": st(interp), "unavailable": list(unavailable)}


GOOD = _answer(
    facts=[("Net interest income was TZS 1,191,080 million in FY2025.", ["IS.net_interest_income.2025"])],
    calc=[("Return on equity was 26.9% in FY2025.", ["ratio.roe.2025"]),
          ("The fair value is TZS 2,354.07 against a last close of TZS 2,040.00.", ["valuation.fair_value", "price.last"])],
    interp=[("The model view is Inconclusive because it depends on the cost-of-equity method.", ["model_view"])])


def test_no_provider_configured_is_ai_unavailable_and_nothing_is_called(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    out = assistant.ask("Why is ROE high?", REPORT)
    assert out["status"] == "AI_UNAVAILABLE" and "ANTHROPIC_API_KEY" in out["reason"]


def test_a_grounded_answer_is_shown_with_its_evidence():
    client = FakeClient(GOOD)
    out = assistant.ask("How profitable is it?", REPORT, client=client)
    assert out["status"] == "ANSWERED"
    ev = out["source_facts"][0]["evidence"][0]
    assert ev["kind"] == "SOURCE_FACT" and ev["source"] == "Test AR 2025, page 150" and ev["value"] == "1191080"
    assert out["calculated_results"][0]["evidence"][0]["how"] == "profit / average equity"
    assert "may be wrong" in out["note"]


def test_the_request_is_grounded_cached_structured_and_has_a_refusal_fallback():
    client = FakeClient(GOOD)
    assistant.ask("How profitable is it?", REPORT, client=client)
    sent = client.sent
    assert sent["model"] == "claude-opus-5-5"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert sent["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in sent["betas"]
    context_block, question_block = sent["messages"][0]["content"]
    assert context_block["cache_control"] == {"type": "ephemeral"}
    assert "IS.net_interest_income.2025" in context_block["text"] and "How profitable" not in context_block["text"]
    assert question_block["text"].endswith("How profitable is it?")


def test_the_context_is_identical_for_the_same_run(monkeypatch):
    """Byte-identical context is what lets the prompt cache hit on the second question."""
    from packages.copilot.context import context_text
    assert context_text(build_context(REPORT)) == context_text(build_context(json.loads(json.dumps(REPORT))))


@pytest.mark.parametrize("bad, why", [
    (_answer(facts=[("Net interest income was TZS 1,250,000 million.", ["IS.net_interest_income.2025"])]), "1250000"),
    (_answer(calc=[("ROE was 31.5%.", ["ratio.roe.2025"])]), "31.5"),
    (_answer(calc=[("Fair value is TZS 2,354.07.", ["valuation.dcf_value"])]), "do not exist"),
    (_answer(interp=[("Loans grew about 18% a year.", ["model_view"])]), "18"),
    (_answer(facts=[("The bank is well run.", [])]), "cites no context entry"),
])
def test_an_invented_number_or_citation_withholds_the_whole_answer(bad, why):
    out = assistant.ask("Tell me about it", REPORT, client=FakeClient(bad))
    assert out["status"] == "UNGROUNDED", out
    assert any(why in p for p in out["problems"])
    assert "source_facts" not in out and "interpretation" not in out


def test_a_number_from_the_question_may_be_repeated():
    ans = _answer(interp=[("A cost of equity of 15% would be higher than the configured method.", ["coe.value"])])
    out = assistant.ask("What if the cost of equity were 15%?", REPORT, client=FakeClient(ans))
    assert out["status"] == "ANSWERED"


def test_a_question_the_context_cannot_answer_says_so():
    ans = _answer(answerable=False, unavailable=["Return on equity for FY2024: equity for FY2023 not extracted"])
    out = assistant.ask("What was ROE in 2024?", REPORT, client=FakeClient(ans))
    assert out["status"] == "NOT_ANSWERABLE" and "not extracted" in out["unavailable"][0]


def _req():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _resp(code):
    return httpx2.Response(code, request=_req())


@pytest.mark.parametrize("client, reason", [
    (FakeClient(raises=anthropic.APIConnectionError(request=_req())), "could not be reached"),
    (FakeClient(raises=anthropic.APITimeoutError(request=_req())), "did not answer in time"),
    (FakeClient(raises=anthropic.RateLimitError("busy", response=_resp(429), body=None)), "busy"),
    (FakeClient(raises=anthropic.AuthenticationError("bad key", response=_resp(401), body=None)), "credentials"),
    (FakeClient(raises=anthropic.InternalServerError("oops", response=_resp(500), body=None)), "(500)"),
    (FakeClient(GOOD, stop="refusal"), "declined"),
    (FakeClient(GOOD, stop="max_tokens"), "cut off"),
    (FakeClient("this is not json"), "required form"),
    (FakeClient({"answerable": True}), "required form"),
])
def test_every_provider_failure_is_ai_unavailable(client, reason):
    out = assistant.ask("Anything", REPORT, client=client)
    assert out["status"] == "AI_UNAVAILABLE" and reason in out["reason"]


def test_decimals_and_strings_build_the_same_context():
    live = json.loads(json.dumps(REPORT))
    live["valuation"]["result"]["fair_value"] = Decimal("2354.070325")
    a = {e["key"]: e["display"] for e in build_context(live)["entries"]}
    b = {e["key"]: e["display"] for e in build_context(REPORT)["entries"]}
    assert a == b


def test_numbers_inside_labels_are_not_read_as_figures():
    from packages.copilot.grounding import _numbers
    assert _numbers("In FY2025 the RA-20261007-001 run") == []           # not 25, not 20261007
    assert [n for n, _ in _numbers("TZS 1,191,080 million and 26.9%")] == [Decimal("1191080"), Decimal("26.9")]
