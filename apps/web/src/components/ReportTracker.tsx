"use client";

import { useEffect } from "react";
import { captureEvent } from "../lib/telemetry";

export function ReportTracker({ symbol }: { symbol: string }) {
  useEffect(() => {
    captureEvent("report_opened", { symbol });
  }, [symbol]);

  return null;
}
