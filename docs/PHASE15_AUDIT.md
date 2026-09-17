# Phase 15 Repository Audit: Evidence-Backed Data Gateway

## 1. Current Architecture State
- **Asset Universe**: The \AssetUniverseEngine\ supports DSE discovering well, but CMSA and Bank of Tanzania (BoT) fallback to manual mocking in \PRODUCTION\ because we lack direct APIs. Phase 14 left this as a physical blocker.
- **Evidence Model**: The existing evidence tracking simply stores UUIDs of documents. It does not enforce a rigid workflow (SOURCE CHECK → FORMAT CHECK → UNIT CHECK) for human-entered data.
- **Authentication**: Placeholder NextAuth logic exists, but rigid RBAC (Role-Based Access Control) for \USER\ vs \VERIFIER\ is missing.
- **Source Conflict Engine**: Completely missing. Currently, the system assumes a single source of truth per metric.
- **Document Extraction**: Docling is heavily integrated for PDF extraction, but dual-validation (Docling + Camelot) table comparisons are not implemented.

## 2. Phase 15 Objectives
Instead of building a simple "manual override" form to bypass the missing BoT/CMSA APIs, we must construct a deeply audited **Evidence Gateway**. 
If a user wants to input the T-Bill 364-day yield because the BoT API is down, they cannot just type "14.5%". They must submit:
1. The 14.5% value.
2. The exact URL to the BoT auction PDF.
3. The page and table number.
4. And a \VERIFIER\ role must approve it, or the \Camelot\ extraction engine must cross-validate it.

## 3. Structural Adjustments Needed
- \packages/evidence_gateway/\ module must be built.
- \packages/database/models.py\ must expand to include \EvidenceSubmission\, \SourceRegistry\, and \SourceConflict\.
- \connectors/bot/\ and \connectors/cmsa/\ must be built to scrape HTML/PDF directly instead of waiting for a clean JSON API.
