"use client";

// The signed-in account as the web server reports it (/api/session/me forwards the httpOnly cookie to the API).
// Loaded once per page view and shared by every component that asks. Plan and features are for showing the
// right buttons only: the API checks the entitlement itself on every request.
import { useEffect, useState } from "react";

export type Account = {
  id: number;
  email: string;
  role: "user" | "admin";
  plan: { id: string; name: string };
  features: string[];
};

type State = { status: "loading" | "ready"; user: Account | null };

let pending: Promise<Account | null> | null = null;

function load(): Promise<Account | null> {
  if (!pending) {
    pending = fetch("/api/session/me", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : { user: null }))
      .then((b) => (b?.user ?? null) as Account | null)
      .catch(() => null);
  }
  return pending;
}

export function refreshAccount() {
  pending = null;
}

export function useAccount(): State {
  const [state, setState] = useState<State>({ status: "loading", user: null });
  useEffect(() => {
    let live = true;
    load().then((user) => live && setState({ status: "ready", user }));
    return () => {
      live = false;
    };
  }, []);
  return state;
}
