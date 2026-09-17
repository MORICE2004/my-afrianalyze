# Tanzania Data Matrix

This document outlines the data sources, their availability, freshness, and evidence mechanisms for the Tanzania asset classes in My AfriAnalyze.

| Asset Class | Source | Status | Freshness | Evidence |
|-------------|--------|--------|-----------|----------|
| Government Bonds | Bank of Tanzania (BoT) | ACTIVE | Daily/Weekly | BoT PDF Reports (`EvidenceRecord`) |
| Corporate Bonds | Dar es Salaam Stock Exchange (DSE) | ACTIVE | Daily | DSE Market Reports (`EvidenceRecord`) |
| Equities | Dar es Salaam Stock Exchange (DSE) | ACTIVE | Daily | DSE Daily Trading Reports (`EvidenceRecord`) |
| Mutual Funds (UTT AMIS) | UTT AMIS Website / Reports | ACTIVE | Daily | UTT AMIS NAV Publications (`EvidenceRecord`) |
| Macroeconomic Data | Bank of Tanzania (BoT) / NBS | ACTIVE | Monthly/Quarterly | Official BoT / NBS Bulletins (`EvidenceRecord`) |
| FX Rates | Bank of Tanzania (BoT) | ACTIVE | Daily | BoT Exchange Rate Publications (`EvidenceRecord`) |

## Evidence Integration
Every financial calculation in the system relies on an `EvidenceRecord` to trace the data point back to its original source document. If a value cannot be traced back to an explicit data release, it is marked as `UNAVAILABLE`.
