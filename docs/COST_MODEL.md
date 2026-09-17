# My AfriAnalyze - Cost Model

This document outlines the expected cost structure for running the My AfriAnalyze platform.

## 1. LLM Cost (Inference & Reasoning)
- **Model**: Assumed use of OpenAI GPT-4o or similar high-tier reasoning models for unstructured text processing (e.g., annual reports, complex filings).
- **Token Usage per Document**:
  - Input tokens: ~50,000 - 100,000 tokens (for 150-300 page annual reports parsed via Docling).
  - Output tokens: ~2,000 - 5,000 tokens (for structured extraction into Pydantic schemas).
- **Cost Estimate per Document**: ~$0.25 - $0.50 per report.
- **Cost per Bank/Company (Annually)**: 1 Annual Report + 4 Quarterly Reports + 2 Earnings Calls = ~$2.00 - $3.50 per company per year.

## 2. Extraction Cost (Docling Integration)
- **Infrastructure**: Running Docling requires memory-intensive instances (e.g., 8GB+ RAM per worker for PDF parsing).
- **Compute Cost**: If hosted on AWS (e.g., t3.large or m5.large instances) or equivalent cloud provider.
- **Cost Estimate**: Assuming 10 hours of processing time per month across all target companies. ~$0.10/hour = $1.00 - $5.00/month for document extraction compute.

## 3. Database Cost
- **Structured Data (PostgreSQL)**: To store time-series financial data, ratios, and historical prices.
  - Instance: Basic managed PostgreSQL (e.g., AWS RDS db.t4g.micro or db.t3.small)
  - Cost Estimate: ~$15 - $30 / month.
- **Document/Vector Storage**: If storing vector embeddings for semantic search of reports.
  - Cost Estimate: ~$5 - $15 / month (e.g., Pinecone starter or pgvector on same RDS instance).
- **Total DB Cost Estimate**: ~$20 - $45 / month.

## 4. Research-Run Cost (End-to-End Execution)
A "Research-Run" represents running the entire pipeline (Extract -> Validate -> Calculate -> Value -> Report) for a single company or a batch.
- **Compute (Data pipelines, Valuation Engine)**: Minimal cost, largely CPU-bound math operations. ~$0.01 per run.
- **API Costs**: Any paid APIs for live market prices (e.g., African exchange data APIs, if not scraped/free). Assuming $50/month for minimal exchange data access.
- **LLM Synthesis**: Generating the final research report (Input: 20k tokens of data, Output: 2k tokens report) = ~$0.10.

### Total Estimated Cost for a Full Platform Update (10 Companies)
- **LLM Parsing/Extraction**: $5.00
- **Compute Pipeline**: $1.00
- **Final Report Generation**: $1.00
- **Total Run Cost**: ~$7.00 per full market update.
- **Fixed Monthly Costs (DB, APIs, Hosting)**: ~$75.00 - $100.00 / month.
