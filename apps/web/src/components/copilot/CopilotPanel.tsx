"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";
import { ErrorState } from "@/components/ui/NotAvailable";
import { apiGet, type Security } from "@/lib/api";

interface Evidence { key: string; kind: string; label: string; display: string; period?: string; source?: string; how?: string }
interface Item { text: string; evidence: Evidence[] }
interface Reply {
  status: "ANSWERED" | "NOT_ANSWERABLE" | "UNGROUNDED" | "AI_UNAVAILABLE";
  reason?: string; run_id?: string; source_facts?: Item[]; calculated_results?: Item[]; interpretation?: Item[];
  unavailable?: string[]; note?: string;
}

const EXAMPLES = [
  "Why is this company valued this way?",
  "Why has return on equity changed?",
  "What are the major risks?",
  "How sensitive is fair value to the discount rate?",
];

function Section({ title, kind, items }: { title: string; kind: string; items?: Item[] }) {
  if (!items || items.length === 0) return null;
  return (
    <section className="space-y-2" data-testid={`copilot-${kind}`}>
      <h3 className="text-xs font-mono uppercase tracking-widest text-neutral-500">{title}</h3>
      <ul className="space-y-3">
        {items.map((it, i) => (
          <li key={i} className="text-sm">
            <p>{it.text}</p>
            <details className="mt-1 text-xs text-neutral-600">
              <summary className="cursor-pointer">Where this comes from ({it.evidence.length})</summary>
              <ul className="mt-1 space-y-1 pl-3 border-l border-neutral-200">
                {it.evidence.map((e) => (
                  <li key={e.key}>
                    <span className="font-mono">{e.kind}</span> · {e.label}: <span className="font-mono">{e.display}</span>
                    {e.period && <> · {e.period}</>}{e.source && <> · {e.source}</>}{e.how && <> · {e.how}</>}
                  </li>
                ))}
              </ul>
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}

// Asks through this site's /api/copilot route, which carries the sign-in cookie to the API.
export function CopilotPanel() {
  const [companies, setCompanies] = useState<Security[] | null>(null);
  const [securityId, setSecurityId] = useState("");
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState<Reply | null>(null);
  const [error, setError] = useState<{ status: number | null; message: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet<{ results: Security[] }>("/api/v1/securities").then((r) => {
      const withReports = r.ok ? r.data.results.filter((s) => s.has_report) : [];
      setCompanies(withReports);
      if (withReports[0]) setSecurityId(withReports[0].id);
    });
  }, []);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setReply(null);
    setError(null);
    try {
      const res = await fetch("/api/copilot", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ security_id: securityId, question }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const d = body?.detail;
        setError({ status: res.status, message: Array.isArray(d) ? d.map((x: { msg: string }) => x.msg).join(". ") : d ?? `Request failed (${res.status})` });
      } else {
        setReply(body as Reply);
      }
    } catch {
      setError({ status: null, message: "The site could not be reached." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={ask} className="space-y-3 border border-neutral-200 bg-white p-4" data-testid="copilot-form">
        <label className="block text-sm">
          <span className="font-medium">Company</span>
          <select value={securityId} onChange={(e) => setSecurityId(e.target.value)} aria-label="Company"
            className="mt-1 block w-full border border-neutral-300 px-2 py-2 text-sm">
            {companies === null && <option>Loading…</option>}
            {companies?.map((c) => <option key={c.id} value={c.id}>{c.id} · {c.name}</option>)}
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium">Question</span>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} minLength={3} maxLength={1000} required rows={3}
            aria-label="Question" className="mt-1 block w-full border border-neutral-300 px-3 py-2 text-sm" />
        </label>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((q) => (
            <button key={q} type="button" onClick={() => setQuestion(q)} className="border border-neutral-300 px-2 py-1 text-xs">{q}</button>
          ))}
        </div>
        <button type="submit" disabled={busy || !securityId} className="bg-black text-white px-4 py-2 text-sm font-semibold disabled:opacity-50">
          {busy ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && (error.status === 401 ? (
        <p className="text-sm" role="alert">
          <Link href="/login" className="underline font-semibold">Sign in</Link> to ask the research assistant. Each question costs money
          to answer, so it is limited per account.
        </p>
      ) : (
        <ErrorState message={error.message} />
      ))}

      {reply && (
        <div className="border border-neutral-200 bg-white p-4 space-y-5" data-testid="copilot-reply" data-status={reply.status}>
          {reply.status === "AI_UNAVAILABLE" && (
            <p className="text-sm"><span className="font-semibold">AI unavailable.</span> {reply.reason} The research report itself is unaffected.</p>
          )}
          {reply.status === "UNGROUNDED" && (
            <p className="text-sm"><span className="font-semibold">Answer withheld.</span> {reply.reason} Try asking more narrowly, or read the report.</p>
          )}
          {reply.status === "NOT_ANSWERABLE" && (
            <p className="text-sm font-semibold">The research data for this company does not contain the answer.</p>
          )}
          <Section title="From the documents" kind="facts" items={reply.source_facts} />
          <Section title="Calculated by AfriEdge" kind="calculated" items={reply.calculated_results} />
          <Section title="Interpretation (AI-written)" kind="interpretation" items={reply.interpretation} />
          {reply.unavailable && reply.unavailable.length > 0 && (
            <section>
              <h3 className="text-xs font-mono uppercase tracking-widest text-neutral-500">Not available</h3>
              <ul className="list-disc pl-5 text-sm">{reply.unavailable.map((u, i) => <li key={i}>{u}</li>)}</ul>
            </section>
          )}
          {reply.note && <p className="text-xs text-neutral-500">{reply.note}{reply.run_id && <> Research run {reply.run_id}.</>}</p>}
        </div>
      )}
    </div>
  );
}
