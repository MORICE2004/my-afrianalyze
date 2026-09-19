# Draft: request to the DSE for historical market data (academic route)

DRAFT for the owner to review, complete and send. Claude Code has not sent anything.

- Items in [brackets] need your details.
- Please check the current DSE Data Vending Policy (academic use, clauses 17.1 and 17.7 as read on 2026-09-17)
  before sending. The clause numbers and conditions may have changed.

**To:** Dar es Salaam Stock Exchange PLC, Market Data / Data Vending Office
**Subject:** Request for historical end-of-day data for academic research (Data Vending Policy, academic use)

Dear Sir or Madam,

I am [name], [role] at [university / institution]. I am writing to request access to historical DSE market data
for academic, non-commercial research. The request is made under the academic-use provisions of the DSE Data
Vending Policy.

**Purpose.** We are studying how to value listed Tanzanian banks, starting with NMB Bank Plc and CRDB Bank Plc.
This includes estimating equity beta for thinly traded shares with methods designed for infrequent trading
(Dimson and Scholes-Williams). These methods need daily prices, volumes and index levels over several years.

**Data requested** (end of day, [start date, e.g. 1 January 2019] to [end date]):

1. Daily closing price, traded volume and number of deals for NMB Bank Plc (NMB) and CRDB Bank Plc (CRDB).
2. Daily closing levels of the DSE All Share Index (DSEI) and the Tanzania Share Index (TSI).
3. Corporate actions over the same period (dividends, bonus issues, rights issues, splits).
4. [Optional: the same fields for other listed banks, if permitted.]

**How the data will be used.**

- To calculate statistics such as beta, return volatility and the share of days without trades.
- The raw prices will not be republished or redistributed.
- Results will cite the DSE as the source.
- We will follow any attribution, storage, retention and publication conditions the DSE sets. Please let us
  know whether published research outputs derived from the data (for example a beta estimate or a valuation)
  are permitted, and whether that changes if a research report is shared with the public.

**Format.** CSV or Excel, one file per instrument, with the date, close, volume and deals columns.

Please tell me whether any fee, agreement or supporting letter from [institution] is required. I can provide
[proof of enrolment / employment, research outline, supervisor letter].

Yours faithfully,
[name]
[role, institution]
[email, phone]

---

**After you receive the data.** Each file can be loaded with its licence reference, which is stored with every
price:

```powershell
.venv\Scripts\python -m pipelines.dse.import_prices --instrument DSE:NMB --file path\to\nmb.xlsx --licence "DSE academic access, ref ..."
```

This unblocks the share price, beta, cost of equity, valuation, target price and model view for each bank.
