"""Ask the research copilot a question about one research run.

Statuses returned (never an exception to the caller):
  ANSWERED        grounded answer: every number traced to a cited context entry
  NOT_ANSWERABLE  the context does not contain what the question needs (the model says so)
  UNGROUNDED      the model's answer cited something absent, or a number the entries do not support; withheld
  AI_UNAVAILABLE  no provider configured, timeout, rate limit, provider error, refusal, or unusable output

The deterministic research product does not depend on any of this: reports, valuations and portfolios work
the same when the provider is down. Logs carry the status, timing and token counts, never the question.
"""
from __future__ import annotations

import json
import logging
import os
import time

from pydantic import ValidationError

from packages.copilot.context import build_context, context_text
from packages.copilot.grounding import Answer, check
from packages.core.config import settings

log = logging.getLogger("afriedge.copilot")

SYSTEM = """You are AfriEdge's research copilot. You explain one company's research to an investor.

You know only the JSON context in the user's message: entries with a key, a kind and a display text.
- SOURCE_FACT: read from a document or the exchange, with its document and page.
- CALCULATED: computed by AfriEdge's deterministic engines; "how" says how.
- STATUS: something that is not available, and why.

Rules:
1. Use only the entries. If the question needs something that is not there, set answerable to false or list
   it under "unavailable", using the STATUS reasons. Never estimate, recall or compute a figure yourself.
2. Every statement cites the keys it rests on. Write every number exactly as the cited entry's display text
   shows it. Do not convert units, round differently or derive new numbers (no sums, differences or growth
   rates that are not already an entry).
3. Keep the three kinds apart: source_facts only from SOURCE_FACT entries, calculated_results only from
   CALCULATED entries, interpretation for what they mean (no numbers that are not in the entries it cites).
4. If entries disagree, or the model view is Inconclusive, say so plainly.
5. This is research and education, not investment advice. Do not tell the reader to buy or sell."""

_STATEMENT = {"type": "object", "additionalProperties": False, "required": ["text", "keys"],
              "properties": {"text": {"type": "string"}, "keys": {"type": "array", "items": {"type": "string"}}}}
SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["answerable", "source_facts", "calculated_results", "interpretation", "unavailable"],
          "properties": {"answerable": {"type": "boolean"},
                         "source_facts": {"type": "array", "items": _STATEMENT},
                         "calculated_results": {"type": "array", "items": _STATEMENT},
                         "interpretation": {"type": "array", "items": _STATEMENT},
                         "unavailable": {"type": "array", "items": {"type": "string"}}}}


def _unavailable(reason: str, **extra) -> dict:
    return {"status": "AI_UNAVAILABLE", "reason": reason, **extra}


def provider_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def _client():
    import anthropic

    # One retry: a question should fail fast to AI_UNAVAILABLE rather than hang a page for minutes.
    return anthropic.Anthropic(timeout=60.0, max_retries=1)


def ask(question: str, report: dict, client=None) -> dict:
    """`report` is a research run's snapshot (or a live report in development)."""
    ctx = build_context(report)
    meta = {"run_id": ctx["run_id"], "security_id": ctx["security_id"], "model": settings.COPILOT_MODEL}
    if client is None:
        if not provider_configured():
            return _unavailable("The research copilot has no AI provider configured (ANTHROPIC_API_KEY is not set). "
                                "Every figure on the report is still available.", **meta)
        client = _client()

    import anthropic

    started = time.perf_counter()
    try:
        response = client.beta.messages.create(
            model=settings.COPILOT_MODEL,
            max_tokens=8000,
            system=SYSTEM,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            # On a safety decline the API re-runs the request on a fallback model inside the same call.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": [
                # Stable per run, so repeat questions about the same company read it from the prompt cache.
                {"type": "text", "text": "<context>" + context_text(ctx) + "</context>",
                 "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": "Question: " + question},
            ]}],
        )
    except anthropic.AuthenticationError:
        log.error("copilot: provider rejected the credentials")
        return _unavailable("The AI provider rejected AfriEdge's credentials.", **meta)
    except anthropic.PermissionDeniedError:
        log.error("copilot: credentials lack permission for %s", settings.COPILOT_MODEL)
        return _unavailable("The AI provider refused access to the configured model.", **meta)
    except anthropic.RateLimitError:
        return _unavailable("The AI provider is busy (rate limited). Try again in a minute.", **meta)
    except anthropic.APITimeoutError:
        return _unavailable("The AI provider did not answer in time.", **meta)
    except anthropic.BadRequestError as exc:
        log.error("copilot: request rejected by the provider: %s", exc.message)
        return _unavailable("The AI provider rejected the request.", **meta)
    except anthropic.APIStatusError as exc:
        log.warning("copilot: provider error %s", exc.status_code)
        return _unavailable(f"The AI provider returned an error ({exc.status_code}).", **meta)
    except anthropic.APIConnectionError:
        return _unavailable("The AI provider could not be reached.", **meta)

    elapsed = round(time.perf_counter() - started, 2)
    usage = getattr(response, "usage", None)
    meta |= {"seconds": elapsed, "model_used": getattr(response, "model", None),
             "tokens": None if usage is None else {
                 "input": getattr(usage, "input_tokens", None), "output": getattr(usage, "output_tokens", None),
                 "cache_read": getattr(usage, "cache_read_input_tokens", None)}}
    log.info("copilot: stop=%s seconds=%s tokens=%s", response.stop_reason, elapsed, meta["tokens"])

    if response.stop_reason == "refusal":
        return _unavailable("The AI provider declined to answer this question.", **meta)
    if response.stop_reason == "max_tokens":
        return _unavailable("The answer was cut off before it finished.", **meta)
    text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), None)
    try:
        answer = Answer.model_validate(json.loads(text or ""))
    except (json.JSONDecodeError, ValidationError):
        return _unavailable("The AI provider's answer was not in the required form.", **meta)

    problems = check(answer, ctx, question)
    if problems:
        log.warning("copilot: answer withheld, %d grounding problem(s)", len(problems))
        return {"status": "UNGROUNDED", **meta,
                "reason": "The answer was withheld because it was not fully supported by the research data.",
                "problems": problems}

    by_key = {e["key"]: e for e in ctx["entries"]}

    def cited(statements):
        return [{"text": s.text, "evidence": [by_key[k] for k in s.keys]} for s in statements]

    return {"status": "ANSWERED" if answer.answerable else "NOT_ANSWERABLE", **meta,
            "source_facts": cited(answer.source_facts), "calculated_results": cited(answer.calculated_results),
            "interpretation": cited(answer.interpretation), "unavailable": answer.unavailable,
            "note": "Source facts and calculated results come from AfriEdge's stored data; interpretation is "
                    "AI-written and may be wrong. Not investment advice."}
