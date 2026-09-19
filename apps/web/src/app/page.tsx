import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { SecuritySearch } from "@/components/SecuritySearch";
import { ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type Security } from "@/lib/api";

export const metadata: Metadata = {
  title: "Search listed companies",
  description: "Search DSE, NSE and USE companies by ticker or name and open the sourced research report.",
};

export default async function HomePage() {
  const res = await apiGet<{ results: Security[] }>("/api/v1/securities");

  return (
    <div className="flex flex-col items-center pt-10 sm:pt-20">
      <div className="w-full max-w-3xl">
        <h1 className="text-3xl sm:text-4xl font-light tracking-tight text-neutral-900 mb-3 text-center">
          African equity research, <span className="font-semibold">sourced line by line</span>
        </h1>
        <p className="text-center text-sm text-neutral-600 mb-8">
          Every figure links to the page of the document it came from. If a figure cannot be sourced, the page says so.
        </p>
        <SecuritySearch />

        <section className="mt-12" aria-labelledby="coverage">
          <h2 id="coverage" className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-3">
            Security master
          </h2>
          {!res.ok ? (
            <ErrorState message={res.error} />
          ) : (
            <ul className="divide-y divide-neutral-200 border border-neutral-200 bg-white">
              {res.data.results.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm">
                  <span>
                    <span className="font-mono font-semibold">{s.id}</span>
                    <span className="ml-3 text-neutral-700">{s.name}</span>
                    <span className="ml-3 text-xs text-neutral-500">{s.currency}</span>
                  </span>
                  {s.has_report ? (
                    <Link href={`/report/${encodeURIComponent(s.id)}`} className="text-xs font-semibold underline underline-offset-4">
                      Open report
                    </Link>
                  ) : (
                    <span className="text-xs text-neutral-500">No report yet</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
