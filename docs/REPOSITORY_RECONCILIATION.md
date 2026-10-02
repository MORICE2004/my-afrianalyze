# Repository reconciliation

Done 2026-09-25 under the owner's canonical-repository directive. Evidence for every "Quality", "Real data"
and "Security" cell is in `docs/LEGACY_AFRIEDGE_FORENSIC_REPORT.md` and `docs/AFRIEDGE_PRODUCTION_AUDIT.md`.

## What exists

Searched the Desktop, Documents, Downloads and `~/.gemini` (four levels deep) for `afrianalyz*` and
`afriedge*`, and listed every branch on GitHub (`MORICE2004`). `my-afrianalyzesvg` does not exist locally
or on GitHub.

| Repository | Branch | Purpose | Quality | Real data | Security | Deployment | Decision |
|---|---|---|---|---|---|---|---|
| `Desktop/Git hub repos/my-afrianalyze` → `MORICE2004/my-afrianalyze` | `m3-crdb-report` (`957ab54` at the start of this work) | v1 Tanzania research product: NMB and CRDB reports, DSE prices, sourced valuation | CI 5/5 green; 222 local tests; migrations tested on Postgres | yes: 592 figures from 10 annual reports, each two-reader agreed and on its cited page; 2,473 price days per bank | production guards, secret and dependency scans clean; no sign-in (none needed yet) | Vercel protected preview | **CANONICAL** |
| same remote | `afriedge-production-baseline` (`957ab54`) | Backup of the canonical branch before reconciliation | as above | as above | as above | none | keep, do not develop on it |
| `~/.gemini/antigravity/scratch/my-afrianalyze` → same remote | `master` (`b77c609`, clean working tree; identical to `origin/master`) | "AfriEdge" rebrand and UI from another agent, 5 commits since the split (`193c2ba`, 2026-09-17) | self-certified; CI claim false (no runs existed) | **no**: data pages hardcoded or random; copilot fed invented "audited" figures | fake sign-in (any password is "J Smith", every API caller is user 1) | three failed Vercel production deploys (2026-09-24) | **UNTRUSTED LEGACY / REFERENCE**. Not deleted, not overwritten |
| same remote | `afriedge-legacy-archive` (`b77c609`) | Backup of `master` as it stood | as above | as above | as above | none | keep as the archive |
| same remote | `truth-pass/nmb-vertical-slice` (`b96d840`) | Earlier stage of the canonical work | superseded | contained in `m3-crdb-report` (checked with `git merge-base --is-ancestor`) | | none | obsolete; safe to delete later, not deleted |
| `Desktop/AfriAnalyzer` | none (not a git repository) | empty folder | | | | | nothing to do |
| `Downloads/afrianalyze-claude-code-kit` | none | the rules kit (`CLAUDE.md`, `docs/`) the project was started from | | | | | reference only |

## Which is newer, which is safer

- **Newer:** `m3-crdb-report` (2026-09-25) has 27 commits since the split; `master` has 5 (last 2026-09-24).
- **Safer and truthful:** `m3-crdb-report`. Every figure it shows comes from a stored, sourced record; the
  legacy pages show numbers typed into the page source (forensic report).
- **Valuable in the legacy line:** the AfriEdge name and logo. The rest is presentation that does not call
  the API, and several components compute or fake financial figures in the browser.

## Decision

`m3-crdb-report` stays canonical. It was chosen on correctness, security, real data, tests and deployment
evidence, not on appearance. From the legacy line only the logo and the brand name are ported
(forensic report, "Salvage"). No legacy data, sign-in, API response, status text or CI claim is ported.

`master` is not rewritten or force-pushed. When the owner is ready, the plan is to make `master` match the
canonical branch with an ordinary merge commit that takes the canonical side, so the legacy history stays
readable in git and in `afriedge-legacy-archive`. That is a separate, deliberate step.
