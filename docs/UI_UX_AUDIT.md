# UI/UX Audit: My AfriAnalyze Frontend

## Overview
This document serves as the preliminary UX/UI audit for the My AfriAnalyze Next.js application prior to the major Phase 22 Redesign. 

## 1. What Exists
- **Framework**: Next.js (App Router).
- **Core Pages**: Homepage (pp/page.tsx), Dashboard (pp/dashboard/page.tsx), Portfolio Wizard (pp/portfolio/page.tsx), Company Report (pp/report/[symbol]/page.tsx).
- **Components**: AIValuations.tsx, RecommendationBadge.tsx, PortfolioDashboard.tsx, ResearchTimeline.tsx, EvidenceViewer.tsx, TechnicalChart.tsx, FinancialMetrics.tsx.
- **Styling**: Tailwind CSS (globals.css).
- **Telemetry**: PostHog integrated (lib/posthog.ts).
- **Auth**: NextAuth configured.

## 2. What Works
- The basic routing and folder structure is correctly established.
- The separation of concerns between Portfolio, Research, and Dashboard is logically sound.
- Components for core functionalities (AI Valuations, Evidence, Timeline) physically exist.
- NextAuth and PostHog are successfully stubbed/integrated.

## 3. What Looks Weak / Missing
- **Design System**: Lacks a cohesive, centralized design system (shadcn/ui or Tremor are not yet fully leveraged). Styling is likely fragmented one-off Tailwind classes.
- **Information Architecture**: The current navigation does not explicitly guide the user through the complex African Market Universe (Markets -> Companies -> Funds -> Fixed Income -> Portfolios).
- **Dashboard Density & Visual Polish**: The existing PortfolioDashboard and AIValuations components lack the professional density, typography, and visual clarity of institutional tools like FinSight AI or Bloomberg terminals.
- **Evidence Traceability UX**: While EvidenceViewer.tsx exists, the workflow from a top-level financial metric down to the underlying PDF document is not seamlessly integrated.
- **Empty & Error States**: Missing robust, human-readable error handling and aesthetically pleasing empty states (e.g., "No portfolio yet").
- **Dark Mode**: No explicit sophisticated dark mode theme configured.
- **Mobile Responsiveness**: Highly complex financial tables and charts likely break or overflow on 320px-430px screens.

## 4. Required Transformations
- Overhaul the Tailwind configuration to include strict design tokens (colors, typography, spacing).
- Implement a professional sidebar/top-nav layout suitable for complex SaaS.
- Refactor the component library to heavily utilize Tremor (for analytical charts/cards) and shadcn/ui (for forms, navigation, buttons, dialogs).
- Build the dedicated analytical workspaces: Ratio Dashboard, Technical Workspace, Valuation Explainer, and Portfolio Stress Testing.
- Ensure 100% preservation of deterministic data, evidence pipelines, and existing API hooks.
