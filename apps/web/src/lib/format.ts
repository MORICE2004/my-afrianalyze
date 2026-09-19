export function fmtMillions(v: number): string {
  const abs = Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
  return v < 0 ? `(${abs})` : abs;
}

export function fmtPerShare(v: number): string {
  return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtValue(v: number, unit: string): string {
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
