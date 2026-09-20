# Compliance notes: open questions for a lawyer

FOR LAWYER REVIEW. This file lists questions only. It contains no legal conclusions, and nothing here should
be read as legal advice (PRODUCT_CONTEXT.md section 71, ROADMAP Milestone 7).

Last updated: 2026-09-20.

## Owner decisions recorded (not legal advice)

| Date | Decision | Effect in the product |
|---|---|---|
| 2026-09-19 | The owner's position is that showing target prices and BUY / HOLD / SELL labels does not need a licence | `SHOW_TRADE_LABELS` is now on by default. The disclaimer still appears on every report and PDF. The setting can be switched off |
| 2026-09-19 | Use the DSE academic route for price data | A draft request is in `DSE_ACADEMIC_DATA_REQUEST.md`. The owner sends it. It is still unsent |
| 2026-09-19 | Use the prices the DSE serves publicly on its own website rather than waiting for a licence, accepting the terms-of-use risk. The owner's words: the data are available online and the product needs to be built | Daily prices and index levels for NMB and CRDB are loaded from `dse.co.tz`, whose `robots.txt` disallows nothing. No login, paywall or CAPTCHA is involved. **The DSE Data Vending Policy (cl. 16.3.3, 23.1) restricts reuse of DSE market data, so this is a known, accepted risk, not a cleared one.** Each price carries the web address, download time and file hash, so the series can be withdrawn if the DSE objects. The files are never served on (HTTP 403): the product calculates from the data and does not republish it |
| 2026-09-19 | The owner reviews and approves research runs for now. Target flow: a user requests a report, the system prepares it, the owner reviews it, then users can see it | Only runs approved with `pipelines.review approve` are shown in production. The request queue is not built yet |

The questions below remain open. A written confirmation from the CMSA, or a lawyer's opinion, would document the
licensing position if it is ever questioned.

## What the product does today (facts for the reviewer)

- It publishes research reports on listed Tanzanian companies (first: NMB Bank Plc). The reports contain
  figures extracted from the company's annual reports, ratios, cost-of-equity inputs, and cited risk
  statements.
- It shows the last traded share price from the DSE's public data, with the address it came from and the time
  it was downloaded. The price file itself is not served to users.
- Once beta can be measured from that price history, it also shows:
  - a fair value range and a 12-month target price;
  - a "model view": Undervalued, Fairly valued or Overvalued, from a fixed rule comparing expected total
    return with the cost of equity.
- BUY / HOLD / SELL labels sit behind a setting (`SHOW_TRADE_LABELS`). It is on since the owner's decision of
  2026-09-19. A label is only shown when there is a target price behind it.
- Every report and PDF carries this disclaimer: "For research and education only. This is not investment
  advice, an offer, or a solicitation to buy or sell any security."
- A named person must approve each research run before it is shown in production. The run is logged with
  their name, the date and a note.
- A planned portfolio wizard will suggest securities and amounts for a given capital, risk profile and horizon.
- Planned business model: free basic research, paid individual plans (mobile money), group plans, broker or
  institution plans.

## Investment advice and research licensing

Tanzania (Capital Markets and Securities Authority, CMSA):

1. Does publishing company research, fair values or target prices to the public count as investment advice or
   an investment adviser business under the Capital Markets and Securities Act and its regulations?
2. Does the answer change between:
   - "Undervalued / Fairly valued / Overvalued" and "BUY / HOLD / SELL";
   - free and paid access;
   - public and subscriber-only access?
3. Does the portfolio wizard (specific securities and amounts for a user's capital) need a different licence
   from research reports?
4. If a licence is needed, which category, what capital, what qualified persons, and which conduct rules
   apply (record keeping, conflicts of interest, suitability, complaints)?
5. Is there an exemption for educational or general (non-personalised) research? What conditions would the
   product need to meet?
6. Must the approving reviewer be a licensed or qualified person? Must reports name the reviewer?
7. Is the current disclaimer wording adequate? What else must appear (risk warnings, conflicts, methodology,
   date of the price used)?
8. Are there rules on the timing of research relative to company announcements, or on restricted periods?

Kenya (Capital Markets Authority) and Uganda (Capital Markets Authority), for later expansion:

9. The same questions 1 to 8 for Kenya and Uganda, including any rules on cross-border research distribution.

## Data rights

10. **Dar es Salaam Stock Exchange market data.**
    - Does showing end-of-day prices, historical prices or index levels (including delayed data) need a DSE
      data licence?
    - Would using them only to compute beta and valuations, without displaying them, need one?
    - Does this project qualify for the academic route (Data Vending Policy cl. 17.1 and 17.7)?
    - If it does, can results be shown in a paid product?
11. **Company annual reports** (NMB Bank Plc investor relations page):
    - May figures be extracted from annual reports and republished with page citations?
    - May copies of the PDF be hosted on our server (we currently serve stored copies so each number can link
      to its page), or must we only link to the company's site?
12. **Bank of Tanzania** (bond auction results, Monetary Policy Committee statements) and **National Bureau of
    Statistics** (CPI releases):
    - Any restrictions or attribution requirements for commercial reuse?
13. **Damodaran Online** (NYU Stern country risk premium tables):
    - May these published figures be used in a paid product?
    - What attribution is required?
14. What attribution text is required for each source, and where must it appear (page, PDF, footer)?

## Personal data (for when accounts exist)

15. Which obligations apply under the Tanzania Personal Data Protection Act 2022 to accounts, saved portfolios
    and alerts (registration, consent, data location, cross-border transfer, retention)?
16. The same for the Kenya Data Protection Act 2019 and the Uganda Data Protection and Privacy Act 2019, when
    expanding.
17. Are portfolio holdings "sensitive" personal data needing extra safeguards?

## Payments (for when the owner starts Milestone 6)

18. Which licences or agreements are needed to take subscription payments by mobile money and card in
    Tanzania? How should VAT be handled on digital subscriptions?
