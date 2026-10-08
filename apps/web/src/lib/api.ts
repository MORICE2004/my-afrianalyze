// Client for the AfriEdge API. Every call returns either data or an error
// the UI can show. There is no fallback data anywhere in the frontend.

// The browser calls the public URL. Server-side rendering can use a different address, e.g. the API's
// service name inside Docker (API_URL_INTERNAL=http://api:8000); it falls back to the public URL.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const SERVER_API_URL = (process.env.API_URL_INTERNAL ?? API_URL).replace(/\/$/, "");

function baseUrl(): string {
  return typeof window === "undefined" ? SERVER_API_URL : API_URL;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number | null; error: string };

export async function apiGet<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    // In the browser, pass the visitor's analytics choice (lib/consent.ts). Server renders send none.
    const consent: Record<string, string> = typeof document !== "undefined" && /(?:^|; )afriedge_consent=[^;]*%22analytics%22%3Atrue/.test(document.cookie)
      ? { "X-Analytics-Consent": "granted" } : {};
    const res = await fetch(`${baseUrl()}${path}`, { cache: "no-store", ...init, headers: { ...consent, ...(init?.headers as Record<string, string> | undefined) } });
    const body = await res.json().catch(() => null);
    if (!res.ok) {
      return { ok: false, status: res.status, error: body?.detail ?? `Request failed (${res.status})` };
    }
    return { ok: true, data: body as T };
  } catch {
    return {
      ok: false,
      status: null,
      // Readers are not shown the service's address; the server log has the detail.
      error: "The data service is not reachable right now. No figures are shown while it is offline.",
    };
  }
}

export async function apiPost<T>(path: string, payload: unknown): Promise<ApiResult<T>> {
  return apiGet<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}


// ------------------------------------------------------------------ types

// Data status words from CLAUDE.md. A figure without VERIFIED or PARTIALLY_VERIFIED is never shown as a number.
export type DataStatus =
  | "VERIFIED"
  | "PARTIALLY_VERIFIED"
  | "INSUFFICIENT_DATA"
  | "BLOCKED"
  | "STALE"
  | "CONFLICTING_SOURCE";

export type Unavailable = { available: false; reason: string; status?: DataStatus };

export interface Security {
  photo?: LibraryPhoto | null;
  id: string;
  exchange: string;
  exchange_name?: string;
  country?: string | null;
  country_code?: string | null;
  ticker: string;
  isin: string | null;
  name: string;
  sector: string;
  currency: string;
  is_bank: boolean;
  listing_url: string;
  verified_at: string;
  verification_note?: string | null;
  has_report?: boolean;
  industry_template?: string;
  listing_status?: string;
}

export interface HealthSource {
  source: string;
  status: string;
  fresh: boolean;
  last_success_at: string | null;
  age_hours: number | null;
  max_age_hours: number;
  detail: string;
}

export type RegistryState = "OK" | "STALE" | "FAILED" | "PARTIAL" | "NEVER_RUN" | "COMING" | "NOT_BUILT";

// One source from config/source_registry.json, merged with its loaders' live records by the API.
export interface RegistrySource {
  id: string;
  name: string;
  country: string;
  datasets: string;
  state: RegistryState;
  parser_state: "IMPLEMENTED" | "NOT_BUILT";
  coverage: "V1" | "COMING";
  licensing: string;
  licensing_note: string;
  last_success_at: string | null;
  last_retrieval_at: string | null;
  last_failure_at: string | null;
  probe: { result: string; checked_at: string; detail?: string } | null;
}

export interface Health {
  status: "online" | "degraded" | "offline";
  checked_at: string;
  database: { ok: boolean; detail?: string };
  sources: HealthSource[];
  registry?: RegistrySource[];
  summary?: string;
}

export interface DocRef {
  document_id: number;
  title: string;
  page: number | null;
  url: string;
  viewer_url?: string; // AfriEdge's page viewer; absent for sources not shown, such as exchange price files
  sha256: string | null;
  retrieved_at: string;
}

export type Computed = {
  available: true;
  value: number;
  formula: string;
  inputs: Record<string, number | null>;
  status?: DataStatus;
};
export type Maybe<T> = (T & { available: true }) | Unavailable;

export interface FactCell {
  available: true;
  value: number;
  status?: DataStatus;
  unit?: string;
  currency?: string;
  period_end?: string;
  label_as_reported?: string;
  source?: DocRef;
  method?: string;
  agreed_by?: string[];
  column?: string;
  derived?: string;
  restated?: { id: number; detail: string }[];
}

export interface StatementRow {
  item_code: string;
  label: string;
  unit: "TZS_millions" | "TZS_per_share" | string;
  derived?: string;
  cells: Record<string, FactCell | (Unavailable & { conflicts?: number[] })>;
  analysis: {
    rows: {
      fiscal_year: number;
      value: number;
      yoy: Computed | Unavailable;
      common_size: Computed | Unavailable | null;
    }[];
    cagr: Computed | Unavailable;
    first_year: number;
    last_year: number;
  } | null;
  note: { text: string; numbers: number[]; rule: string } | null;
  section: string;
}

export interface BetaEstimate {
  available: boolean;
  reason?: string;
  beta?: number;
  std_error?: number | null;
  r_squared?: number | null;
  observations?: number;
  [k: string]: unknown;
}

export interface CoeInput {
  value: number;
  label: string;
  source_name: string;
  source_url: string;
  as_of: string;
  attributes?: Record<string, unknown>;
  age_days?: number;
  status?: DataStatus;
}

export interface Scenario {
  probability: number;
  drivers: Record<string, number>;
  shocks: Record<string, number>;
  fair_value: number;
  target_price_12m: number;
  dps_next_12m: number;
  methods: Record<string, { available: boolean; per_share?: number; formula?: string; reason?: string; [k: string]: unknown }>;
  projection: Record<string, number>[];
}

export interface ReviewState {
  run_id: string | null;
  status: "draft" | "in_review" | "published" | "superseded" | "none";
  created_at?: string;
  reviewer: string | null;
  reviewed_at?: string | null;
  data_sha256?: string;
  config_sha256?: string;
}

export interface Report {
  generated_at: string;
  disclaimer: string;
  review: ReviewState;
  data_as_of: { fiscal_year_end: string | null; latest_report: string | null; published_on: string | null; retrieved_at: string | null };
  status_counts: { verified: number; partially_verified: number; conflicting_source: number; insufficient_data: number };
  trade_labels_enabled: boolean;
  capital_basis: "bank" | "consolidated" | null;
  security: Security;
  header: {
    price: Maybe<{ value: number; trade_date: string; currency: string; source: DocRef; attribution?: string }>;
    recommendation: Maybe<{
      model_view: "Undervalued" | "Fairly valued" | "Overvalued" | "Inconclusive";
      // Set when the view flips with the cost-of-equity method: the configured method's view, and why.
      selected_model_view?: "Undervalued" | "Fairly valued" | "Overvalued";
      inconclusive_reason?: string;
      // Only present when the SHOW_TRADE_LABELS setting is on (section 71).
      trade_label?: "BUY" | "HOLD" | "SELL";
      expected_total_return: number;
      price_upside: number;
      dividend_yield: number;
      thresholds: { above: number; below: number; buy_margin: number; sell_margin: number };
      rule: string;
      trade_labels_enabled: boolean;
    }>;
    target_price: Maybe<{ value: number }>;
    fair_value_range: Maybe<{ low: number; high: number }>;
    confidence: { score: number; level: string; notes: string[] };
  };
  years: number[];
  statements: { code: string; title: string; rows: StatementRow[] }[];
  ratios: { code: string; label: string; values: Record<string, Computed | Unavailable> }[];
  beta: {
    benchmark: string;
    estimates: Record<string, BetaEstimate>;
    zero_volume: { available: boolean; value?: number; reason?: string; zero_volume_days?: number; index_trading_days?: number };
    selected: { available: boolean; method?: string; beta?: number; raw_beta?: number; reason?: string; skipped?: string[] };
    rule: Record<string, unknown>;
    adjustments: string[];   // share splits applied to the price series, in words
  };
  // Descriptive technical indicators (packages/analysis/technical.py). Never used by the valuation.
  technical: {
    available: boolean; status: DataStatus; reason?: string;
    last_close?: number | string; last_trade_date?: string; age_days?: number; stale?: boolean; split_adjusted?: boolean;
    liquidity: { window: number; zero_volume_days: number; max_zero_volume_share: number | string };
    indicators?: Record<string, Record<string, unknown>>;
    note?: string;
  };
  cost_of_equity: {
    inputs: Record<string, CoeInput | null>;
    method: { subtract_default_spread: boolean; crp_scaling: string; sensitivity_betas: number[]; risk_free_series: string };
    result: { available: boolean; value?: number; formula?: string; reason?: string; status?: DataStatus; steps?: { label: string; value: number; ref?: string }[] };
    sensitivity: { available: boolean; rows?: { beta: number; cost_of_equity: number }[]; reason?: string };
    alternatives?: { treatment: string; formula?: string; cost_of_equity?: number | string | null; fair_value?: number;
      target_price_12m?: number; model_view?: string | null }[];
  };
  valuation: {
    result: { available: boolean; reason?: string; status?: DataStatus; fair_value?: number; target_price_12m?: number; expected_dps_12m?: number;
      fair_value_range?: { low: number; high: number }; scenarios?: Record<string, Scenario>; target_formula?: string;
      structure?: Record<string, number> };
    // Decimals arrive as strings; coerce with Number() before numeric methods such as toFixed.
    sensitivity: { available: boolean; reason?: string; rows?: { beta: number | string; cost_of_equity: number; fair_value: number; range_low: number; range_high: number }[] };
    base_drivers: Record<string, { available: boolean; value?: number; reason?: string; basis: string; formula?: string; inputs?: Record<string, number> }>;
    config: {
      horizon_years: number;
      history_window_years: number;
      terminal_growth: { value: number; kind: string; note: string };
      method_weights: Record<string, number>;
      scenarios: Record<string, { probability: number; shocks: Record<string, number>; narrative_rule: string }>;
    };
  };
  recommendation_rule: { buy_margin: number; sell_margin: number; _comment?: string };
  peers: Unavailable;
  risks: { id: number; category: string; title: string; quote: string; source: DocRef }[];
  checks: { fiscal_year: number; name: string; passed: boolean; detail: string }[];
  conflicts: {
    id: number; fiscal_year: number; item_code: string; kind: string;
    value_a: number | null; source_a: string; value_b: number | null; source_b: string;
    detail: string; status: string; source: DocRef | null;
  }[];
  sources: {
    documents: (DocRef & {
      kind: string; fiscal_year: number | null; publisher: string; listing_url: string | null;
      published_on?: string | null; published_on_evidence?: string | null; terms_note?: string | null;
    })[];
    macro: { series_id: string; label: string; value: number; unit: string; as_of: string; source_name: string; source_url: string; retrieved_at: string }[];
    reference: { key: string; label: string; value: number; unit: string; as_of: string; source_name: string; source_url: string }[];
  };
  gaps: string[];
}

// ------------------------------------------------------------------ prices, markets, research stream

type Num = number | string;

// The latest stored close (apps/api/routers/market.py). timing is CURRENT or STALE, never LIVE.
export type Quote =
  | {
      available: true; security_id: string; currency: string; status: DataStatus;
      price: Num; trade_date: string; previous_close: Num | null; previous_date: string | null;
      change: Num | null; change_pct: Num | null; traded: boolean; last_traded_date: string | null;
      volume: Num | null; turnover: Num | null; high: Num | null; low: Num | null; market_cap: Num | null;
      timing: "CURRENT" | "STALE"; public_label: string;
      freshness: { age_days: number; latest_session: string; max_age_days: number; kind: string };
      licensing: string; attribution: string | null;
      source: { document_id: number; publisher: string; title: string; url: string; retrieved_at: string | null } | null;
      reconciliation: { status: string; provider_a: string; close_a: Num; provider_b: string; close_b: Num;
        difference_pct: Num; checked_at: string } | null;
      split_adjusted_change: boolean;
    }
  | { available: false; security_id: string; currency: string; status: DataStatus; reason: string;
      public_label: string; public_reason: string; licensing?: string };

export type PriceSeries =
  | { available: true; instrument_id: string; points: { date: string; close: Num; volume: Num | null }[];
      notes: string[]; first: string | null; last: string | null; attribution: string }
  | { available: false; instrument_id: string; status: DataStatus; reason: string; public_reason: string };

export type IndexSummary =
  | { id: string; name: string; available: true; value: Num; trade_date: string; change_1d: Num;
      change_1m: Num | null; change_ytd: Num | null; change_1y: Num | null; excluded_days: number }
  | { id: string; name: string; available: false; status: DataStatus; reason: string };

export type Mover = { security_id: string; name: string; close: Num; change: Num; volume: Num };

export interface MarketsOverview {
  markets: {
    market: string; name: string; exchange: string; currency: string; securities_in_master: number;
    index: ({ available: true; id: string; value: Num; trade_date: string; change: Num; change_1m?: Num | null;
      change_ytd?: Num | null; change_1y?: Num | null; attribution?: string })
      | { available: false; id: string; status: DataStatus; reason: string; public_reason: string };
    macro?: { available: boolean; reason?: string; attribution?: string;
      rows?: { indicator: string; label: string; value: Num; unit: string; year: number }[] };
  }[];
  session: { exchange: string; latest_session: string | null; kind: string; note: string };
  activity:
    | { available: true; trade_date: string; currency: string; turnover: Num; volume: Num; securities_traded: number;
        securities_stored: number; market_cap: Num; coverage: string; attribution: string }
    | { available: false; status: DataStatus; reason: string; public_reason?: string };
  sectors: { available: boolean; indices?: IndexSummary[]; basis?: string; reason?: string; public_reason?: string };
  commentary: { available: boolean; reason: string };
  movers: {
    available: boolean; reason?: string; trade_date?: string; coverage?: string; attribution?: string; note?: string;
    breadth?: { up: number; down: number; unchanged: number; no_trade: number; not_updated: number };
    gainers?: Mover[]; losers?: Mover[];
  };
}

export type ResearchStage = {
  stage: string; state: string; detail: string; critical: boolean; duration_ms: number;
  recorded?: boolean; executed_at?: string | null;
};

export type StreamEvent =
  | { event: "step"; step: string; state: string; label: string; duration_ms: number }
  | { event: "security"; data: Security }
  | { event: "quote"; data: Quote }
  | { event: "stage"; data: ResearchStage }
  | { event: "report"; data: Report }
  | { event: "unavailable"; status: string; reason: string }
  | { event: "done"; total_ms: number };

// ------------------------------------------------------------------ news (pipelines/news.py → news_items)

// An openly licensed photo from AfriEdge's library (pipelines/images.py): the institution or city, not an event.
export interface LibraryPhoto {
  kind: "library"; url: string; width: number; height: number; caption: string; author: string; licence: string;
  licence_url: string | null; source_page: string; source: string;
}

export type Relevance = "HIGH" | "MEDIUM" | "LOW" | "NOT_ASSESSED";
export interface NewsItem {
  id: string; title: string; url: string; language: string; published_at: string; retrieved_at: string;
  summary: string | null; countries: string[]; categories: string[]; relevance: Relevance; relevance_reason: string;
  image: { url: string; width: number; height: number; credit: string; rights: "PERMITTED"; retrieved_at: string | null } | null;
  photos: LibraryPhoto[];
  source: { id: string; name: string; tier: number | null; tier_label: string | null };
  companies: { security_id: string; name: string; link: "named" | "sector" }[];
}
export interface NewsList {
  items: NewsItem[]; count: number; categories: string[];
  sources: { name: string; tier: number; connected: boolean }[];
  some_sources_unavailable: boolean; notice: string | null; relevance_method: string; terms: string;
  lead_id: string | null; lead_rule: string;
}
export interface NewsDetail extends NewsItem {
  markets: { country: string; exchange: string; currency: string }[];
  indicators: ({ series_id: string; label: string } & ({ available: true; value: string; unit: string; date: string; source_url: string } | { available: false; reason: string }))[];
  related_companies: { security_id: string; name: string; ticker: string; exchange: string; currency: string; link: string; why: string }[];
  why_it_matters: string | null; caution: string;
}
