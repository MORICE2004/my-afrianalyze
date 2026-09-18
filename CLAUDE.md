# My AfriAnalyze: Rules for Claude Code

An African investment research and portfolio intelligence platform. AI explains. Deterministic code calculates. Every number has a source.

## Read before any work

1. `docs/PRODUCT_CONTEXT.md`: the full vision (sections 1 to 69) and addendum (70 to 82). Source of truth.
2. `docs/ROADMAP.md`: milestones with acceptance checks.
3. `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`: the current truth about the repo (create it first if it doesn't exist).
4. `docs/KNOWN_GAPS.md` and `docs/PROGRESS.md`.

Never trust an earlier "complete", "live" or "production ready" claim. Verify.

## Non-negotiable rules

1. **No fabricated data.** If it can't be verified, show a status (`VERIFIED`, `PARTIALLY_VERIFIED`, `INSUFFICIENT_DATA`, `BLOCKED`, `STALE`, `CONFLICTING_SOURCE`) and no number.
2. **Pipeline order:** Source → Validated Data → Deterministic Calculation → Research Context → AI Interpretation. An LLM never computes or overwrites a financial figure.
3. **Provenance:** every value carries amount, currency, unit, period, source (URL/document, page, table), retrieval time and validation status.
4. **Money:** `Decimal` in Python, `NUMERIC` in Postgres. No floats for money. FX conversion is explicit (rate, timestamp, source).
5. **Time:** store observation date, publication date and availability date. No look-ahead.
6. **Thin markets:** zero-volume days are recorded. Beta and technical indicators follow section 74.
7. **Recommendations:** trade labels sit behind `SHOW_TRADE_LABELS` (default off). Every view is traceable and shows uncertainty. Disclaimers everywhere (section 71).
8. **Human review** before anything is published (section 72).
9. **Data rights:** respect source terms. Never bypass logins, paywalls, CAPTCHAs or robots rules (section 73).
10. **Secrets** live in environment variables or Secret Manager. Never in git. No PII or raw documents in PostHog, Sentry or logs.

## Status words (use exactly)

`REAL`, `MOCKED`, `PARTIAL`, `BLOCKED`, `UNTESTED`, `BROKEN`, `MISSING`. Never say "production ready" without the certification matrix in section 64.

## How to work

For every major change: audit → plan → implement → test → adversarial test → verify (including in the browser) → document → commit → report.

- Check `git status`, branch and recent commits before big changes. Don't discard uncommitted work.
- One branch per milestone or P0 item. Small, clear commits.
- Use subagents for independent work, then verify their output yourself.
- After the audit and after each P0 item: commit, update `docs/PROGRESS.md` and `docs/KNOWN_GAPS.md`, post a plain-language report. Keep going unless a decision is needed.
- Ask the owner before: legal or licensing text, paid services, using a source with unclear terms, deleting data, changing the stack, or a valuation method choice with material impact.
- Say plainly when something is broken, over-engineered, impossible, or when data doesn't exist.

## Scope right now

Version 1 is Tanzania only: DSE equities (NMB and CRDB first), Bank of Tanzania T-bills and bonds, verifiable unit trust funds, TZS only (section 77). No payment code until the owner says so.

## Environment

- The owner's machine runs Windows. Use PowerShell-friendly commands or Docker.
- The owner isn't a professional programmer. Explain results simply.

## Project map and commands

(Fill this in during the audit and keep it current: folder layout, how to start each service, how to run each test suite, env variables needed, where each engine lives.)
