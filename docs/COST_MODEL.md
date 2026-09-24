# AfriEdge Production Cost Drivers & Budget Model

## 1. Cost Drivers

| Service | Driver | Expected Unit Cost | Monthly Estimate (Base Tier) |
|---|---|---|---|
| **Vercel Pro** | Edge hosting, Next.js compute | $20/month per seat | $20.00 |
| **GCP Cloud Run (API)** | Container CPU/RAM on demand | ~$0.00002400 / vCPU-second | $15.00 - $35.00 |
| **Managed PostgreSQL (Neon)** | Storage & Compute hours | Compute: $0.16/hour, Storage: $0.000164/GB-hr | $19.00 |
| **Managed Redis (Upstash)** | Requests / Data storage | Free tier (up to 10k req/day), then $0.20/100k req | $5.00 - $10.00 |
| **LLM Inference (LiteLLM)** | AI Copilot research grounding | Gemini 1.5 Flash: $0.35 / 1M tokens; Claude Sonnet: $3.00 / 1M tokens | $15.00 - $50.00 |
| **Total Estimated Operating Cost** | | | **$74.00 - $134.00 / month** |

## 2. Optimization Safeguards
1. **Deterministic Calculations First:** Financial metrics, ratios, DCF valuations, and portfolio math never invoke an LLM. Pure Python execution saves ~85% of potential token costs.
2. **Result Caching:** Research summaries and parsed financial filings are cached in Redis with an 86,400s (24h) TTL.
