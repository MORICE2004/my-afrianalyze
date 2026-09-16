# Open-Source Ecosystem Audit

This document evaluates the existing open-source ecosystem to determine what components should be reused, integrated, or referenced for the My AfriAnalyze platform.

## 1. OpenBB Platform
- **Repository:** https://github.com/OpenBB-finance/OpenBB
- **Purpose:** Investment research platform consolidating financial data.
- **License:** AGPL-3.0 (Core Platform). Some SDKs/tools are MIT.
- **Maturity:** High. Very active community and well-established.
- **Useful components:** Data standardization patterns, API structures, data provider interfaces.
- **Risks:** Copyleft (AGPL) license means integrating its core into our proprietary backend could trigger open-source requirements for our platform. Heavy dependency on US/Euro-centric data models.
- **Recommended usage:** Use as an architectural reference for financial schemas and data provider abstractions. Do not directly embed the core platform code into our proprietary application to avoid AGPL pollution.
- **Decision:** **Reference Only**.

## 2. OpenBB AI/Agent Tooling (e.g., OpenBB Terminal)
- **Repository:** https://github.com/OpenBB-finance/OpenBBTerminal (now largely transitioned to OpenBB Platform/Workspace)
- **Purpose:** Agentic workflows for financial data.
- **License:** AGPL-3.0 / MIT (depending on specific sub-repo).
- **Maturity:** Medium-High.
- **Useful components:** Examples of LLM function calling with financial APIs.
- **Risks:** Similar AGPL copyleft risks for certain components. Lack of specific tools for African markets.
- **Recommended usage:** Study how they structure prompts and function calling for financial agents.
- **Decision:** **Reference Only**.

## 3. Firecrawl
- **Repository:** https://github.com/mendableai/firecrawl
- **Purpose:** Universal web scraping, crawling, and LLM-ready markdown extraction.
- **License:** AGPL-3.0 (Core Engine) / MIT (SDKs).
- **Maturity:** High. Production-ready and actively maintained.
- **Useful components:** High-quality Markdown extraction, web scraping, and content cleaning.
- **Risks:** AGPL-3.0 applies if self-hosting the core engine and modifying it as a service.
- **Recommended usage:** Run as an isolated external service/container (e.g., local endpoint `http://localhost:3002/v1`) and interact via the MIT-licensed SDK. This avoids AGPL pollution of our core proprietary code.
- **Decision:** **Integrate as External Service**.

## 4. Firecrawl Web Agent
- **Repository:** Associated with Firecrawl (typically under the mendableai umbrella).
- **Purpose:** Multi-step browser interactions and dynamic extraction.
- **License:** AGPL-3.0 (Core) / MIT (SDK).
- **Maturity:** Medium.
- **Useful components:** Handling pagination, form fills, and authentication-aware flows for scraping exchange websites (e.g., DSE).
- **Risks:** Same AGPL considerations as Firecrawl. Might be overkill for simple static pages but necessary for complex African exchange portals.
- **Recommended usage:** Run as an isolated external service via API.
- **Decision:** **Integrate as External Service**.

## 5. Docling
- **Repository:** https://github.com/DS4SD/docling
- **Purpose:** Document processing, particularly extracting tables and text from PDFs into structured formats (Markdown, JSON).
- **License:** MIT License.
- **Maturity:** High. Backed by IBM Research.
- **Useful components:** PDF parsing, table extraction, OCR fallback.
- **Risks:** PDF parsing is inherently imperfect, especially for poorly scanned African company annual reports.
- **Recommended usage:** Embed directly into the document ingestion pipeline. Use it as the primary PDF extraction engine.
- **Decision:** **Embed**.

## 6. LangGraph
- **Repository:** https://github.com/langchain-ai/langgraph
- **Purpose:** Stateful, multi-actor orchestration framework for LLMs.
- **License:** MIT License.
- **Maturity:** High. Industry standard for agent orchestration.
- **Useful components:** Stateful graphs, human-in-the-loop, cyclical workflows.
- **Risks:** Can become overly complex if state is not managed carefully.
- **Recommended usage:** Use to orchestrate the multi-agent research team (Company Researcher, Financial Agent, Auditor, etc.) while keeping the state strongly typed.
- **Decision:** **Embed**.

## 7. PydanticAI
- **Repository:** https://github.com/pydantic/pydantic-ai
- **Purpose:** Agent framework leveraging Pydantic for structured generation and validation.
- **License:** MIT License.
- **Maturity:** Medium (newer compared to LangGraph but very promising).
- **Useful components:** Type-safe LLM outputs, deterministic tool calling.
- **Risks:** Ecosystem is still evolving compared to older frameworks.
- **Recommended usage:** Use for individual agent implementations requiring strict schema enforcement (e.g., financial metric extraction) and potentially integrate within LangGraph nodes.
- **Decision:** **Embed**.

## 8. DuckDB
- **Repository:** https://github.com/duckdb/duckdb
- **Purpose:** In-process analytical SQL database.
- **License:** MIT License.
- **Maturity:** High. Very stable and high-performance.
- **Useful components:** Fast analytical queries over extracted data, Pandas integration.
- **Risks:** Not designed for highly concurrent OLTP workloads.
- **Recommended usage:** Use as the analytical engine for number crunching, time-series aggregation, and beta calculations over Parquet/CSV files or dataframes before persisting to PostgreSQL.
- **Decision:** **Embed**.

## 9. Supabase
- **Repository:** https://github.com/supabase/supabase
- **Purpose:** Open-source Firebase alternative (PostgreSQL, Auth, Storage).
- **License:** Apache 2.0.
- **Maturity:** High. Production-ready.
- **Useful components:** PostgreSQL database, Authentication, Row Level Security, S3-compatible Storage.
- **Risks:** Self-hosting the entire stack can be operationally complex.
- **Recommended usage:** Use Supabase Auth for user authentication and authorization. Use its PostgreSQL for the core database and Storage for storing raw PDFs and evidence.
- **Decision:** **Integrate / Use Cloud Offering**.

## 10. Financial Statement/XBRL Parsing Libraries (e.g., Arelle)
- **Repository:** https://github.com/Arelle/Arelle
- **Purpose:** XBRL parsing and validation.
- **License:** Apache 2.0.
- **Maturity:** High.
- **Useful components:** XBRL taxonomy processing.
- **Risks:** African markets (like DSE) often do NOT use XBRL; they publish flat PDFs.
- **Recommended usage:** Keep as a potential future integration if African exchanges adopt XBRL. For now, rely on Docling + LLMs for PDF table extraction.
- **Decision:** **Defer**.

## 11. Market-Data Libraries (e.g., yfinance)
- **Repository:** https://github.com/ranaroussi/yfinance
- **Purpose:** Yahoo Finance market data downloader.
- **License:** Apache 2.0.
- **Maturity:** High.
- **Useful components:** Ticker downloading, price history.
- **Risks:** Yahoo Finance has extremely poor coverage of African exchanges like the DSE. Data is often stale, missing, or inaccurate.
- **Recommended usage:** Do not rely on it as a primary source for African equities. Build custom exchange connectors instead.
- **Decision:** **Reference Only / Fallback**.
