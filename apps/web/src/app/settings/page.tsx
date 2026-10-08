"use client";

import Link from "next/link";
import React, { useState, useSyncExternalStore } from "react";
import { setTheme } from "@/components/layout/ThemeToggle";
import { Panel, ProBadge } from "@/components/ui/kit";
import { useAccount } from "@/lib/account";
import { clearList } from "@/lib/local";

type Choice = "light" | "dark" | "system";

function savedChoice(): Choice {
  try {
    const t = localStorage.getItem("afriedge-theme");
    return t === "light" || t === "dark" ? t : "system";
  } catch {
    return "system";
  }
}

export default function SettingsPage() {
  const { status, user } = useAccount();
  const initial = useSyncExternalStore(() => () => {}, savedChoice, () => "system" as Choice);
  const [choice, setChoice] = useState<Choice | null>(null);
  const current = choice ?? initial;
  const [cleared, setCleared] = useState(false);

  const pick = (c: Choice) => {
    setChoice(c);
    if (c === "system") {
      try {
        localStorage.removeItem("afriedge-theme");
      } catch {
        // storage blocked: nothing to remove
      }
      document.documentElement.setAttribute("data-theme", window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    } else {
      setTheme(c);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>

      <Panel title="Appearance">
        <fieldset>
          <legend className="text-sm text-muted">Theme</legend>
          <div className="mt-2 inline-flex rounded-md border border-line p-0.5" role="radiogroup" aria-label="Theme">
            {(["light", "dark", "system"] as const).map((c) => (
              <button key={c} type="button" role="radio" aria-checked={current === c} onClick={() => pick(c)} data-testid={`theme-${c}`}
                className={`rounded px-3 py-1.5 text-sm capitalize ${current === c ? "bg-selected text-on-selected" : "text-muted hover:text-fg"}`}>
                {c === "system" ? "Match device" : c}
              </button>
            ))}
          </div>
        </fieldset>
      </Panel>

      <Panel title="Account">
        {status === "loading" ? <div className="skeleton h-12" /> : user ? (
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-3"><dt className="text-muted">Email</dt><dd>{user.email}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-muted">Plan</dt>
              <dd className="flex items-center gap-2">{user.plan.name}{user.plan.id === "pro" && <ProBadge />}</dd></div>
            <div className="flex justify-between gap-3"><dt className="text-muted">Excel export</dt>
              <dd>{user.features.includes("excel_export") ? "Included" : "Part of Pro"}</dd></div>
            {user.role === "admin" && (
              <div className="flex justify-between gap-3"><dt className="text-muted">Administration</dt>
                <dd><Link href="/admin" className="underline">Data administration</Link></dd></div>
            )}
          </dl>
        ) : (
          <p className="text-sm text-muted">
            You are not signed in. <Link href="/login" className="underline">Sign in</Link> to keep portfolios. Research pages are
            open to everyone.
          </p>
        )}
      </Panel>

      <Panel title="On this device">
        <p className="text-sm text-muted">Your watchlist and recently viewed companies are kept in this browser only and never sent anywhere.</p>
        <button type="button" onClick={() => { clearList("watchlist"); clearList("recent"); setCleared(true); }}
          className="mt-3 inline-flex h-9 items-center rounded-md border border-line px-3 text-sm hover:bg-surface-2">
          Clear watchlist and history
        </button>
        {cleared && <span role="status" className="ml-3 text-sm text-muted">Cleared.</span>}
      </Panel>
    </div>
  );
}
