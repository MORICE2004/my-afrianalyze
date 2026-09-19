// Client for the My AfriAnalyze API. Every call returns either data or an error
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
    const res = await fetch(`${baseUrl()}${path}`, { cache: "no-store", ...init });
    const body = await res.json().catch(() => null);
    if (!res.ok) {
      return { ok: false, status: res.status, error: body?.detail ?? `Request failed (${res.status})` };
    }
    return { ok: true, data: body as T };
  } catch {
    return {
      ok: false,
      status: null,
      error: `The data service at ${API_URL} is not reachable. No figures are shown while it is offline.`,
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

export function sourceFileUrl(fileUrl: string): string {
  return `${API_URL}${fileUrl}`;
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
  id: string;
  exchange: string;
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

export interface Health {
  status: "online" | "degraded" | "offline";
  checked_at: string;
  database: { ok: boolean; detail?: string };
  sources: HealthSource[];
  summary?: string;
}

export interface DocRef {
  document_id: number;
  title: string;
  page: number | null;
  url: string;
  file_url: string;
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
    price: Maybe<{ value: number; trade_date: string; currency: string; source: DocRef }>;
    recommendation: Maybe<{
      model_view: "Undervalued" | "Fairly valued" | "Overvalued";
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
  };
  cost_of_equity: {
    inputs: Record<string, CoeInput | null>;
    method: { subtract_default_spread: boolean; crp_scaling: string; sensitivity_betas: number[]; risk_free_series: string };
    result: { available: boolean; value?: number; formula?: string; reason?: string; status?: DataStatus; steps?: { label: string; value: number; ref?: string }[] };
    sensitivity: { available: boolean; rows?: { beta: number; cost_of_equity: number }[]; reason?: string };
  };
  valuation: {
    result: { available: boolean; reason?: string; status?: DataStatus; fair_value?: number; target_price_12m?: number; expected_dps_12m?: number;
      fair_value_range?: { low: number; high: number }; scenarios?: Record<string, Scenario>; target_formula?: string;
      structure?: Record<string, number> };
    sensitivity: { available: boolean; reason?: string; rows?: { beta: number; cost_of_equity: number; fair_value: number; range_low: number; range_high: number }[] };
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
