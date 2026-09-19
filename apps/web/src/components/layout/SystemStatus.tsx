"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { apiGet, type Health } from "@/lib/api";

type State = { status: "checking" | Health["status"]; detail: string };

const STYLES: Record<State["status"], { dot: string; label: string }> = {
  checking: { dot: "bg-neutral-300", label: "Checking" },
  online: { dot: "bg-green-500", label: "Online" },
  degraded: { dot: "bg-amber-500", label: "Degraded" },
  offline: { dot: "bg-red-500", label: "Offline" },
};

export function SystemStatus() {
  const [state, setState] = useState<State>({ status: "checking", detail: "Checking the data service" });

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      const res = await apiGet<Health>("/health");
      if (cancelled) return;
      if (!res.ok) {
        setState({ status: "offline", detail: res.error });
      } else {
        const stale = res.data.sources.filter((s) => !s.fresh).map((s) => s.source);
        setState({
          status: res.data.status,
          detail: stale.length ? `Not fresh: ${stale.join(", ")}` : res.data.summary ?? "All sources fresh",
        });
      }
    };
    check();
    const id = setInterval(check, 60_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const s = STYLES[state.status];
  return (
    <Link
      href="/health"
      title={state.detail}
      data-testid="system-status"
      data-status={state.status}
      className="flex items-center gap-2 text-xs text-neutral-600 font-mono tracking-wider uppercase hover:text-black"
    >
      <span className={`w-2 h-2 rounded-full ${s.dot}`} aria-hidden />
      <span>Data: {s.label}</span>
    </Link>
  );
}
