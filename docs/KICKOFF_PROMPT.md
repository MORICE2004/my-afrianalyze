# Kickoff prompt for Claude Code

## Setup (once)

1. Unzip this kit into the root folder of the My AfriAnalyze repo. You should end up with:
   - `CLAUDE.md` in the root (if one already exists, rename the old one to `CLAUDE.old.md` first)
   - `docs/PRODUCT_CONTEXT.md`
   - `docs/ROADMAP.md`
2. Open the repo in Claude Code.
3. Paste the prompt below.

---

## Prompt to paste

You are the principal architect and technical lead for My AfriAnalyze.

Read these files fully before doing anything else:
1. `CLAUDE.md`
2. `docs/PRODUCT_CONTEXT.md` (all 82 sections)
3. `docs/ROADMAP.md`

Then commit these three files on a new branch called `docs-product-context`.

Your first job is the repository truth audit in section 66. Don't write or change application code until the audit is finished.

For the audit:
- Check git status, the current branch and the last 20 commits.
- Inspect every area listed in section 66.
- Search for mocks, stubs, fixtures, fake data, hardcoded financial figures and unfinished code (section 39).
- Start the full stack with Docker and check that the frontend and backend actually talk to each other.
- Run every test suite and record the real results.
- Open the app in a browser at desktop and mobile widths, take screenshots, and confirm or correct each item in section 70.
- Label every capability with one status: REAL, MOCKED, PARTIAL, BLOCKED, UNTESTED, BROKEN or MISSING, with evidence (file and line, command output or screenshot).

Write the results to `docs/MY_AFRIANALYZE_MASTER_AUDIT.md` with these sections: Current state, Real, Mocked, Partial, Blocked, Untested, Broken, Missing, Technical debt, Security issues, Data issues, UX issues, Production blockers. Also fill in the "Project map and commands" section of `CLAUDE.md`.

Then, following section 67, write the P0 to P4 roadmap. Map it onto `docs/ROADMAP.md` (section 81) and keep version 1 limited to Tanzania (section 77). Tell me honestly if any part of the vision is over-engineered for version 1.

Post a plain-language report with:
1. What is actually real today.
2. What earlier summaries claimed that turned out to be false.
3. The P0 list in order.
4. Any decisions you need from me.

Then start P0. After each P0 item, commit and report as section 82 describes.
