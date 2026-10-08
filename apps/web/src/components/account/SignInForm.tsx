"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";

// Posts to this site's own /api/session/* routes, which set an httpOnly cookie. The page never holds the
// session token.
export function SignInForm({ next = "/" }: { next?: string }) {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/session/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail = body?.detail;
        // FastAPI validation errors arrive as a list; show their messages, not the raw structure.
        setError(Array.isArray(detail) ? detail.map((d: { msg: string }) => d.msg).join(". ") : detail ?? "Something went wrong.");
        return;
      }
      router.push(next);
      router.refresh();
    } catch {
      setError("The site could not be reached. Nothing was submitted.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5" data-testid="signin-form">
      <div className="flex gap-6 border-b border-line text-sm" role="tablist">
        {(["login", "signup"] as const).map((m) => (
          <button key={m} type="button" role="tab" aria-selected={mode === m}
            onClick={() => { setMode(m); setError(null); }}
            className={`-mb-px border-b-2 pb-2.5 ${mode === m ? "border-fg font-medium text-fg" : "border-transparent text-muted hover:text-fg"}`}>
            {m === "login" ? "Sign in" : "Create account"}
          </button>
        ))}
      </div>
      <label className="block text-sm">
        <span className="font-medium text-fg">Email</span>
        <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)}
          className="mt-1.5 block h-11 w-full rounded-md border border-line-strong bg-surface px-3 text-[15px] text-fg transition-colors focus:border-fg focus:outline-none" />
      </label>
      <label className="block text-sm">
        <span className="font-medium text-fg">Password</span>
        <input type="password" required minLength={mode === "signup" ? 12 : 1} maxLength={128}
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
          value={password} onChange={(e) => setPassword(e.target.value)}
          className="mt-1.5 block h-11 w-full rounded-md border border-line-strong bg-surface px-3 text-[15px] text-fg transition-colors focus:border-fg focus:outline-none" />
        {mode === "signup" && <span className="mt-1 block text-xs text-muted">At least 12 characters.</span>}
      </label>
      {error && <p role="alert" className="rounded-md bg-neg-bg px-3 py-2 text-sm text-neg">{error}</p>}
      <button type="submit" disabled={busy}
        className="h-11 w-full rounded-md bg-selected text-sm font-medium text-on-selected transition-opacity hover:opacity-90 disabled:opacity-50">
        {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
      </button>
      <p className="text-xs leading-relaxed text-muted">
        There is no password reset yet: it needs an email service, which is not set up. Keep your password safe.
      </p>
    </form>
  );
}
