import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { ReportView } from "@/components/report/ReportView";
import { EmptyState, ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type Report } from "@/lib/api";

function toId(symbol: string): string {
  return decodeURIComponent(symbol).trim().toUpperCase();
}

export async function generateMetadata({ params }: PageProps<"/report/[symbol]">): Promise<Metadata> {
  const { symbol } = await params;
  const id = toId(symbol);
  return {
    title: `${id} research report`,
    description: `Sourced equity research for ${id}: statements, ratios, beta, valuation and risks, each linked to its source.`,
  };
}

export default async function ReportPage({ params }: PageProps<"/report/[symbol]">) {
  const { symbol } = await params;
  const id = toId(symbol);

  if (!/^[A-Z]{2,5}:[A-Z0-9.]{1,12}$/.test(id)) {
    return (
      <EmptyState title="Unrecognised ticker format">
        Reports use the form EXCHANGE:TICKER, for example <Link className="underline" href="/report/DSE%3ANMB">DSE:NMB</Link>.
        You asked for “{decodeURIComponent(symbol)}”.
      </EmptyState>
    );
  }

  const res = await apiGet<Report>(`/api/v1/reports/${encodeURIComponent(id)}`);
  if (!res.ok) {
    if (res.status === 404) {
      return (
        <EmptyState title={`No report for ${id}`}>
          {res.error} <Link className="underline" href="/">Back to search</Link>
        </EmptyState>
      );
    }
    return <ErrorState message={res.error} />;
  }
  return <ReportView report={res.data} />;
}
