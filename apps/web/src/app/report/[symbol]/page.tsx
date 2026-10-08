import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { Workspace } from "@/components/report/Workspace";
import { Empty } from "@/components/ui/kit";
import { apiGet, type Security } from "@/lib/api";

function toId(symbol: string): string {
  return decodeURIComponent(symbol).trim().toUpperCase();
}

export async function generateMetadata({ params }: PageProps<"/report/[symbol]">): Promise<Metadata> {
  const { symbol } = await params;
  const id = toId(symbol);
  const res = /^[A-Z]{2,5}:[A-Z0-9.]{1,12}$/.test(id) ? await apiGet<Security>(`/api/v1/securities/${encodeURIComponent(id)}`) : null;
  const name = res && res.ok ? res.data.name : id;
  return {
    title: `${name} (${id.split(":")[1] ?? id}) research`,
    description: `Sourced research on ${name}: statements, valuation, technicals and risks, each figure linked to its source.`,
  };
}

// The company workspace. The security master answers first (name, ticker, currency), so the header renders on
// the server; the research itself streams in on the page (components/report/Workspace.tsx).
export default async function CompanyPage({ params }: PageProps<"/report/[symbol]">) {
  const { symbol } = await params;
  const id = toId(symbol);

  if (!/^[A-Z]{2,5}:[A-Z0-9.]{1,12}$/.test(id)) {
    return (
      <Empty title="Unrecognised ticker">
        Company pages use the form EXCHANGE:TICKER, for example <Link className="underline" href="/report/DSE%3ANMB">DSE:NMB</Link>.
        You asked for “{decodeURIComponent(symbol)}”. Search for the company instead from the <Link className="underline" href="/research">research page</Link>.
      </Empty>
    );
  }

  const res = await apiGet<Security>(`/api/v1/securities/${encodeURIComponent(id)}`);
  if (!res.ok) {
    if (res.status === 404) {
      return (
        <Empty title={`No listed company matches ${id}`}>
          AfriEdge covers companies listed on the Dar es Salaam Stock Exchange. <Link className="underline" href="/research">Search for a company</Link>.
        </Empty>
      );
    }
    return (
      <Empty title="Research is temporarily unavailable" testId="service-unavailable">
        The data service is not reachable right now, so no figures are shown. Please try again shortly.
      </Empty>
    );
  }
  return <Workspace security={res.data} />;
}
