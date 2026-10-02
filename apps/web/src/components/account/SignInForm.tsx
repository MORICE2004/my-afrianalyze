"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";

// Posts to this site's own /api/session/* routes, which set an httpOnly cookie. The page never holds the
// session token.
export function SignInForm() {
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
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("The site could not be reached. Nothing was submitted.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4 border border-neutral-200 bg-white p-6" data-testid="signin-form">
      <div className="flex gap-4 text-sm font-semibold" role="tablist">
        {(["login", "signup"] as const).map((m) => (
          <button key={m} type="button" role="tab" aria-selected={mode === m}
            onClick={() => { setMode(m); setError(null); }}
            className={`pb-1 border-b-2 ${mode === m ? "border-black text-black" : "border-transparent text-neutral-500"}`}>
            {m === "login" ? "Sign in" : "Create account"}
          </button>
        ))}
      </div>
      <label className="block text-sm">
        <span className="font-medium">Email</span>
        <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full border border-neutral-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-black" />
      </label>
      <label className="block text-sm">
        <span className="font-medium">Password</span>
        <input type="password" required minLength={mode === "signup" ? 12 : 1} maxLength={128}
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
          value={password} onChange={(e) => setPassword(e.target.value)}
          className="mt-1 block w-full border border-neutral-300 px-3 py-2 focus:outline-none focus:ring-1 focus:ring-black" />
        {mode === "signup" && <span className="text-xs text-neutral-500">At least 12 characters.</span>}
      </label>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <button type="submit" disabled={busy}
        className="w-full bg-black text-white py-2 text-sm font-semibold disabled:opacity-50">
        {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
      </button>
      <p className="text-xs text-neutral-500">
        There is no password reset yet: it needs an email service, which is not set up. Keep your password safe.
      </p>
    </form>
  );
}
