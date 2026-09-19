import React from "react";
import type { DataStatus } from "@/lib/api";
import { StatusBadge } from "./StatusBadge";

// Shown wherever a figure cannot be sourced. Always states the reason, and the status when known.
export function NotAvailable({ reason, compact = false, status }: { reason: string; compact?: boolean; status?: DataStatus }) {
  if (compact) {
    if (status) return <StatusBadge status={status} title={reason} />;
    return (
      <span className="text-neutral-400 cursor-help underline decoration-dotted" title={reason}>
        Not available
      </span>
    );
  }
  return (
    <div className="border border-dashed border-neutral-300 bg-neutral-50 px-4 py-3 text-sm text-neutral-600">
      <span className="font-semibold text-neutral-800">Not available.</span>{" "}
      {status && <><StatusBadge status={status} />{" "}</>}
      {reason}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border border-neutral-200 bg-white p-8 text-center">
      <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
      <div className="mt-2 text-sm text-neutral-600 max-w-2xl mx-auto">{children}</div>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  );
}
