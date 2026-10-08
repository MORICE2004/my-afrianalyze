import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { Empty } from "@/components/ui/kit";
import { apiGet } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import { sessionToken } from "@/lib/session";

export const metadata: Metadata = { title: "Source document", robots: { index: false } };

type Meta = { document_id: number; title: string; publisher: string; kind: string; original_url: string; retrieved_at: string | null; sha256: string | null; pages: number };

// Reads a stored source document inside AfriEdge: one page at a time, rendered as an image by the server. The
// original file is not offered; the publisher's own copy is one click away.
export default async function SourceViewer({ params, searchParams }: PageProps<"/sources/[id]">) {
  const { id } = await params;
  const sp = await searchParams;
  if (!/^\d{1,9}$/.test(id)) return <Empty title="Document not found" action={{ label: "Back to research", href: "/research" }} />;
  const token = await sessionToken();
  if (!token) {
    return (
      <div className="mx-auto max-w-xl py-10" data-testid="viewer-signin">
        <Empty title="Sign in to read source documents" action={{ label: "Sign in", href: `/login?next=/sources/${id}` }}>
          Annual reports and other stored sources can be read page by page inside AfriEdge once you are signed in.
          Every figure on a research page still shows its document and page without signing in.
        </Empty>
      </div>
    );
  }
  const res = await apiGet<Meta>(`/api/v1/sources/${id}`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" });
  if (!res.ok) {
    return <Empty title={res.status === 401 ? "Your session has ended" : "Document not available"}
      action={res.status === 401 ? { label: "Sign in again", href: `/login?next=/sources/${id}` } : { label: "Back to research", href: "/research" }}>
      {res.status === 401 ? "Sign in again to keep reading." : "This document is not available to view."}
    </Empty>;
  }
  const m = res.data;
  const raw = Number(Array.isArray(sp.page) ? sp.page[0] : sp.page);
  const page = Number.isInteger(raw) && raw >= 1 && raw <= m.pages ? raw : 1;
  const nav = (p: number, label: string, testId: string) => p >= 1 && p <= m.pages
    ? <Link href={`/sources/${id}?page=${p}`} data-testid={testId} className="inline-flex h-8 items-center rounded-md border border-line px-3 text-sm hover:bg-surface-2">{label}</Link>
    : <span className="inline-flex h-8 items-center rounded-md border border-line px-3 text-sm text-faint">{label}</span>;
  return (
    <div className="mx-auto max-w-4xl pb-10" data-testid="source-viewer">
      <header className="border-b border-line pb-4">
        <div className="text-xs text-muted">Source document · {m.publisher}</div>
        <h1 className="mt-1 text-xl font-semibold tracking-tight">{m.title}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
          <span>{m.pages} pages</span>
          {m.retrieved_at && <span>Retrieved {fmtDate(m.retrieved_at)}</span>}
          {m.sha256 && <span title={m.sha256}>Fingerprint {m.sha256.slice(0, 12)}…</span>}
          <a href={m.original_url.split(" ")[0]} target="_blank" rel="noopener noreferrer" className="font-medium text-fg underline underline-offset-4" data-testid="original-source">
            View the publisher&apos;s original ↗
          </a>
        </div>
      </header>
      <div className="mt-4 flex items-center justify-between gap-3">
        {nav(page - 1, "← Previous", "prev-page")}
        <form action={`/sources/${id}`} className="flex items-center gap-2 text-sm">
          <label htmlFor="pg" className="text-muted">Page</label>
          <input id="pg" name="page" type="number" min={1} max={m.pages} defaultValue={page}
            className="h-8 w-20 rounded-md border border-line bg-surface px-2 text-center tabular-nums" />
          <span className="text-muted">of {m.pages}</span>
        </form>
        {nav(page + 1, "Next →", "next-page")}
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element -- a private, uncached page render, not a static asset */}
      <img src={`/api/source-page/${id}/${page}`} alt={`${m.title}, page ${page}`} data-testid="source-page-image"
        draggable={false}
        className="mt-4 w-full select-none rounded-sm border border-line bg-white" />
      <p className="mt-3 text-xs text-faint">
        Shown for reading inside AfriEdge. The original file is not offered for download here; the publisher&apos;s copy is linked above.
      </p>
    </div>
  );
}
