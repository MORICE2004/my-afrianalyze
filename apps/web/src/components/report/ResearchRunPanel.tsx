"use client";

import React, { useEffect, useState } from "react";
import { EmptyState, ErrorState } from "@/components/ui/NotAvailable";
import { apiGet } from "@/lib/api";
import { fmtDate } from "@/lib/format";

interface Stage { stage: string; state: string; detail: string; critical: boolean; duration_ms: number }
interface Run {
  run_id: string; review_status: string; execution_state: string; created_at: string | null;
  finished_at: string | null; stages: Stage[]; error: string | null; snapshot_sha256: string | null;
  reviewer: string | null; reviewed_at: string | null;
}

const STATE_CLS: Record<string, string> = {
  COMPLETED: "bg-green-100 text-green-900", PARTIAL: "bg-amber-100 text-amber-900",
  FAILED: "bg-red-100 text-red-900", BLOCKED: "bg-red-100 text-red-900",
  INSUFFICIENT_DATA: "bg-neutral-200 text-neutral-800", SKIPPED: "bg-neutral-100 text-neutral-600",
  RUNNING: "bg-blue-100 text-blue-900", QUEUED: "bg-blue-50 text-blue-900", NOT_EXECUTED: "bg-neutral-100 text-neutral-600",
};

function State({ s }: { s: string }) {
  return <span className={`px-2 py-0.5 text-xs font-semibold ${STATE_CLS[s] ?? "bg-neutral-100"}`}>{s.replace("_", " ")}</span>;
}

// The run that produced this research: every stage from the sources to the synthesis, with its state.
export function ResearchRunPanel({ securityId }: { securityId: string }) {
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ runs: Run[] }>(`/api/v1/research-runs?security_id=${encodeURIComponent(securityId)}`).then((r) =>
      r.ok ? setRuns(r.data.runs) : setError(r.error));
  }, [securityId]);

  if (error) return <ErrorState message={error} />;
  if (runs === null) return <p className="text-sm text-neutral-500" aria-live="polite">Loading research runs…</p>;
  const run = runs.find((r) => r.execution_state !== "NOT_EXECUTED");
  if (!run) return <EmptyState title="No executed research run">This research has not been run through the research engine yet.</EmptyState>;

  return (
    <div className="space-y-4" data-testid="research-run">
      <p className="text-sm">
        Run <span className="font-mono">{run.run_id}</span> <State s={run.execution_state} /> · review status{" "}
        <span className="font-semibold">{run.review_status.replace("_", " ")}</span>
        {run.reviewer && <> by {run.reviewer}{run.reviewed_at && <> on {fmtDate(run.reviewed_at)}</>}</>}
        {run.finished_at && <> · finished {fmtDate(run.finished_at)}</>}
      </p>
      {run.error && <ErrorState message={run.error} />}
      <div className="overflow-x-auto border border-neutral-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-xs uppercase tracking-wider text-neutral-500">
            <tr><th className="text-left px-3 py-2">Stage</th><th className="text-left px-3 py-2">State</th><th className="text-left px-3 py-2">Detail</th></tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {run.stages.map((s) => (
              <tr key={s.stage}>
                <td className="px-3 py-2 font-medium">{s.stage.replace("_", " ")}{s.critical && <span className="text-xs text-neutral-500"> · critical</span>}</td>
                <td className="px-3 py-2"><State s={s.state} /></td>
                <td className="px-3 py-2 text-xs text-neutral-700">{s.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-neutral-500">
        A run is never marked completed when a critical stage (sources, documents, extraction, validation, calculations)
        failed. Its report is frozen when it runs{run.snapshot_sha256 && <> (SHA-256 <span className="font-mono">{run.snapshot_sha256.slice(0, 16)}…</span>)</>};
        the published version is exactly what the reviewer approved.
      </p>
    </div>
  );
}
