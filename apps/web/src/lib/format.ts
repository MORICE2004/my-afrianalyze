// Money reaches the browser as a string, because the API keeps exact decimals and JSON numbers
// cannot. So every formatter coerces first: a string's own toLocaleString would return it unchanged,
// which is how "2070" reached the page instead of "2,070.00".
type Num = number | string;

export function fmtMillions(v: Num): string {
  const n = Number(v);
  const abs = Math.abs(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
  return n < 0 ? `(${abs})` : abs;
}

export function fmtPerShare(v: Num): string {
  return Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtValue(v: Num, unit: string): string {
  return unit === "TZS_per_share" ? fmtPerShare(v) : fmtMillions(v);
}

export function fmtPct(v: number, digits = 1): string {
  return `${(v * 100).toFixed(digits)}%`;
}

export function fmtSignedPct(v: number, digits = 1): string {
  const s = (v * 100).toFixed(digits);
  return v > 0 ? `+${s}%` : `${s}%`;
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function unitLabel(unit: string): string {
  if (unit === "TZS_per_share") return "TZS per share";
  if (unit === "TZS_millions") return "TZS millions";
  return unit;
}

// Large amounts in words a reader scans: 2.04 bn, 35.5 tn. Exact figures stay in tables and tooltips.
export function fmtCompact(v: Num): string {
  const n = Number(v);
  const a = Math.abs(n);
  const [d, s] = a >= 1e12 ? [1e12, " tn"] : a >= 1e9 ? [1e9, " bn"] : a >= 1e6 ? [1e6, " m"] : [1, ""];
  return (n / d).toLocaleString("en-US", { maximumFractionDigits: d === 1 ? 0 : 2 }) + s;
}

export function fmtMoney(v: Num, currency: string, digits = 2): string {
  return `${currency} ${Number(v).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

export function fmtNumber(v: Num, digits = 0): string {
  return Number(v).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

// "pos" / "neg" / "flat" for colouring a change. Colour always comes with a sign, never alone.
export function direction(v: Num | null | undefined): "pos" | "neg" | "flat" {
  const n = Number(v);
  if (v === null || v === undefined || Number.isNaN(n) || n === 0) return "flat";
  return n > 0 ? "pos" : "neg";
}

export function fmtShortDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}
