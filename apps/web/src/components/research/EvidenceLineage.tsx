import React from "react";
import { ExternalSource, SourceLink } from "@/components/report/SourceLink";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { Report } from "@/lib/api";
import { fmtDate, fmtPct } from "@/lib/format";

// Every source behind the report, the checks run on the data, and every open conflict.
export default function EvidenceLineage({ report }: { report: Report }) {
  const failed = report.checks.filter((c) => !c.passed);
  const open = report.conflicts.filter((c) => c.kind !== "RESTATEMENT" && c.kind !== "SOURCE_INCONSISTENCY");
  const restated = report.conflicts.filter((c) => c.kind === "RESTATEMENT");
  const sourceIssues = report.conflicts.filter((c) => c.kind === "SOURCE_INCONSISTENCY");

  return (
    <div className="space-y-8">
      <section>
        <h3 className="font-semibold mb-2">Documents</h3>
        <ul className="divide-y divide-neutral-200 border border-neutral-200 bg-white text-sm">
          {report.sources.documents.map((d) => (
            <li key={d.document_id} className="px-4 py-3">
              <SourceLink source={d}>{d.title}</SourceLink>
              <div className="text-xs text-neutral-600 mt-1">
                {d.publisher}
                {d.published_on
                  ? <> · published {fmtDate(d.published_on)} <span title={d.published_on_evidence ?? ""} className="underline decoration-dotted cursor-help">(board approval date)</span></>
                  : " · publication date not found"}
                {" "}· retrieved {fmtDate(d.retrieved_at)} ·{" "}
                <ExternalSource href={d.listing_url ?? d.url}>listing page</ExternalSource>
                <span className="block font-mono text-[11px] text-neutral-500 break-all">SHA-256 {d.sha256}</span>
                {d.terms_note && <span className="block text-[11px] text-neutral-500">Terms: {d.terms_note}</span>}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="font-semibold mb-2">Market and macro inputs</h3>
        <ul className="divide-y divide-neutral-200 border border-neutral-200 bg-white text-sm">
          {report.sources.macro.map((m) => (
            <li key={`${m.series_id}-${m.as_of}`} className="px-4 py-2">
              <span className="font-mono">{fmtPct(m.value, 2)}</span> {m.label} (as of {m.as_of}) —{" "}
              <ExternalSource href={m.source_url}>{m.source_name}</ExternalSource>
            </li>
          ))}
          {report.sources.reference.map((r) => (
            <li key={r.key} className="px-4 py-2">
              <span className="font-mono">{fmtPct(r.value, 2)}</span> {r.label} —{" "}
              <ExternalSource href={r.source_url}>{r.source_name}</ExternalSource>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="font-semibold mb-2">
          Tie checks: {report.checks.length - failed.length} of {report.checks.length} passed
        </h3>
        {failed.length > 0 && (
          <ul className="border border-red-200 bg-red-50 text-sm divide-y divide-red-100">
            {failed.map((c) => (
              <li key={`${c.fiscal_year}-${c.name}`} className="px-4 py-2">FY{c.fiscal_year} {c.name}: {c.detail}</li>
            ))}
          </ul>
        )}
        <details className="mt-2 text-sm">
          <summary className="cursor-pointer text-neutral-600">Show all checks</summary>
          <ul className="mt-2 text-xs font-mono space-y-1">
            {report.checks.map((c) => (
              <li key={`${c.fiscal_year}-${c.name}`}>{c.passed ? "PASS" : "FAIL"} FY{c.fiscal_year} {c.name} — {c.detail}</li>
            ))}
          </ul>
        </details>
      </section>

      {sourceIssues.length > 0 && (
        <section>
          <h3 className="font-semibold mb-2">Figures that do not add up in the source ({sourceIssues.length})</h3>
          <ul className="border border-orange-200 bg-orange-50 text-sm divide-y divide-orange-100" data-testid="source-issues">
            {sourceIssues.map((c) => (
              <li key={c.id} className="px-4 py-2">
                <StatusBadge status="CONFLICTING_SOURCE" /> FY{c.fiscal_year} {c.item_code.replace(/_/g, " ")}: not used in
                any calculation.{" "}
                {c.source && <SourceLink source={c.source}>Open the page</SourceLink>}
                <p className="text-xs text-neutral-700 mt-1">{c.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3 className="font-semibold mb-2">Extraction conflicts ({open.length} open)</h3>
        {open.length === 0 ? (
          <p className="text-sm text-neutral-600">Camelot and Docling agreed on every extracted figure shown in this report.</p>
        ) : (
          <ul className="border border-amber-200 bg-amber-50 text-sm divide-y divide-amber-100" data-testid="conflicts">
            {open.map((c) => (
              <li key={c.id} className="px-4 py-2">
                <b>EXTRACTION_CONFLICT</b> FY{c.fiscal_year} {c.item_code}: {c.detail}
                {c.source && <> — <SourceLink source={c.source}>open page</SourceLink></>}
              </li>
            ))}
          </ul>
        )}
        {restated.length > 0 && (
          <>
            <h4 className="font-semibold mt-4 mb-1 text-sm">Restated comparatives ({restated.length})</h4>
            <ul className="text-xs space-y-1">
              {restated.map((c) => <li key={c.id}>FY{c.fiscal_year} {c.item_code}: {c.detail}</li>)}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
