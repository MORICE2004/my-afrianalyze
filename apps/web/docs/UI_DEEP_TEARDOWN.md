# My AfriAnalyze UI Deep Teardown

## Current State: "Template Slop"
The current dashboard approach suffers from generic "template slop" - it looks like a boilerplate admin dashboard rather than a specialized financial terminal. 
Key issues:
- Low information density: Too much whitespace where data should be.
- Lack of clear hierarchy: Everything feels equally important.
- Misaligned user personas: Tries to serve both casual executives and deep-dive analysts with the same view, failing both.

## The Fix: Persona-Driven Density
We need to split the user experience based on the persona's needs for information density:

### 1. Executive View (The Briefing)
- **Goal:** Quick insights, macro trends, portfolio-level summaries.
- **Density:** Medium. Emphasize key metrics, charts, and plain-text summaries.
- **Layout:** Editorial style, larger typography for key figures, clear "takeaways".

### 2. Analyst View (The Terminal)
- **Goal:** Deep dives, raw data access, comparative analysis, financial modeling.
- **Density:** High. Prioritize data tables, compact metrics, and interactive charts with drill-down capabilities.
- **Layout:** Grid-based, compact, minimal padding, maximizing screen real estate for data.
