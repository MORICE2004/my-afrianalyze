"use client";

import * as Dropdown from "@radix-ui/react-dropdown-menu";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React, { useState } from "react";
import { SecuritySearch } from "@/components/SecuritySearch";
import { refreshAccount, useAccount } from "@/lib/account";
import { ThemeToggle } from "./ThemeToggle";

// Four places to go, and the rest one click away: the research product should be usable without a tour.
export const NAV = [
  { href: "/", label: "Dashboard", match: (p: string) => p === "/" },
  { href: "/markets", label: "Markets", match: (p: string) => p.startsWith("/markets") },
  { href: "/research", label: "Research", match: (p: string) => p.startsWith("/research") || p.startsWith("/report") },
  { href: "/portfolio", label: "Portfolio", match: (p: string) => p.startsWith("/portfolio") || p.startsWith("/dashboard") },
];
export const MORE = [
  { href: "/fixed-income", label: "Fixed income" },
  { href: "/funds", label: "Unit trusts" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/settings", label: "Settings" },
];

function AccountMenu() {
  const { status, user } = useAccount();
  const router = useRouter();
  if (status === "loading") return <span className="skeleton h-9 w-20" aria-hidden />;
  if (!user) {
    return (
      <Link href="/login" className="inline-flex h-9 items-center rounded-md bg-selected px-3 text-sm font-medium text-on-selected hover:opacity-90">
        Sign in
      </Link>
    );
  }
  const signOut = async () => {
    await fetch("/api/session/logout", { method: "POST" });
    refreshAccount();
    router.push("/");
    router.refresh();
  };
  return (
    <Dropdown.Root>
      <Dropdown.Trigger
        className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-2.5 text-sm text-fg hover:bg-surface-2"
        aria-label="Account"
        data-testid="account-menu"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-selected text-xs font-semibold text-on-selected">
          {user.email.slice(0, 1).toUpperCase()}
        </span>
        {user.plan.id === "pro" && <span className="rounded bg-surface-2 px-1.5 text-[11px] font-semibold">Pro</span>}
      </Dropdown.Trigger>
      <Dropdown.Portal>
        <Dropdown.Content align="end" sideOffset={6}
          className="z-50 min-w-52 rounded-lg border border-line bg-surface p-1 text-sm shadow-lg">
          <div className="px-3 py-2 text-xs text-muted">
            <div className="truncate text-fg">{user.email}</div>
            <div>{user.plan.name} plan</div>
          </div>
          <Dropdown.Separator className="my-1 h-px bg-line" />
          <Dropdown.Item asChild><Link href="/dashboard" className="block rounded px-3 py-2 outline-none data-[highlighted]:bg-surface-2">My portfolios</Link></Dropdown.Item>
          <Dropdown.Item asChild><Link href="/settings" className="block rounded px-3 py-2 outline-none data-[highlighted]:bg-surface-2">Settings</Link></Dropdown.Item>
          {user.role === "admin" && (
            <Dropdown.Item asChild><Link href="/admin" className="block rounded px-3 py-2 outline-none data-[highlighted]:bg-surface-2">Data administration</Link></Dropdown.Item>
          )}
          <Dropdown.Separator className="my-1 h-px bg-line" />
          <Dropdown.Item onSelect={signOut} className="cursor-pointer rounded px-3 py-2 outline-none data-[highlighted]:bg-surface-2">
            Sign out
          </Dropdown.Item>
        </Dropdown.Content>
      </Dropdown.Portal>
    </Dropdown.Root>
  );
}

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  // Close the mobile menu whenever the route changes (adjusting state during render, as React recommends).
  const [menuPath, setMenuPath] = useState(pathname);
  if (menuPath !== pathname) {
    setMenuPath(pathname);
    setOpen(false);
  }
  const moreActive = MORE.some((m) => pathname.startsWith(m.href));

  return (
    <div className="flex min-h-screen flex-col bg-background text-fg">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/85">
        <div className="mx-auto flex h-14 max-w-[1320px] items-center gap-3 px-4 sm:px-6">
          <Link href="/" className="flex shrink-0 items-center gap-2 text-[15px] font-semibold tracking-tight">
            <Image src="/logo-mark.png" alt="" width={22} height={19} priority className="dark:invert" />
            AfriEdge
          </Link>
          <nav aria-label="Main" className="ml-4 hidden items-center gap-1 md:flex">
            {NAV.map((n) => {
              const active = n.match(pathname);
              return (
                <Link key={n.href} href={n.href} aria-current={active ? "page" : undefined}
                  className={`rounded-md px-3 py-1.5 text-sm transition-colors ${active ? "bg-surface-2 font-medium text-fg" : "text-muted hover:text-fg"}`}>
                  {n.label}
                </Link>
              );
            })}
            <Dropdown.Root>
              <Dropdown.Trigger className={`inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-colors ${moreActive ? "bg-surface-2 font-medium text-fg" : "text-muted hover:text-fg"}`}>
                More
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><path d="m6 9 6 6 6-6" /></svg>
              </Dropdown.Trigger>
              <Dropdown.Portal>
                <Dropdown.Content align="start" sideOffset={6} className="z-50 min-w-44 rounded-lg border border-line bg-surface p-1 text-sm shadow-lg">
                  {MORE.map((m) => (
                    <Dropdown.Item key={m.href} asChild>
                      <Link href={m.href} className="block rounded px-3 py-2 outline-none data-[highlighted]:bg-surface-2">{m.label}</Link>
                    </Dropdown.Item>
                  ))}
                </Dropdown.Content>
              </Dropdown.Portal>
            </Dropdown.Root>
          </nav>
          <div className="ml-auto hidden w-72 lg:block">
            {!["/", "/research", "/markets"].includes(pathname) && <SecuritySearch size="compact" />}
          </div>
          <div className="ml-auto flex items-center gap-2 lg:ml-0">
            <ThemeToggle />
            <div className="hidden sm:block"><AccountMenu /></div>
            <button
              type="button"
              className="inline-flex h-9 items-center rounded-md border border-line px-3 text-sm md:hidden"
              aria-expanded={open}
              aria-controls="mobile-nav"
              onClick={() => setOpen((o) => !o)}
            >
              {open ? "Close" : "Menu"}
            </button>
          </div>
        </div>
        {open && (
          <div id="mobile-nav" className="border-t border-line bg-surface px-4 pb-4 pt-3 md:hidden">
            <SecuritySearch size="compact" />
            <nav aria-label="Main" className="mt-3 grid grid-cols-2 gap-1">
              {[...NAV, ...MORE].map((n) => (
                <Link key={n.href} href={n.href} aria-current={pathname === n.href ? "page" : undefined}
                  className={`rounded-md px-3 py-2.5 text-sm ${pathname === n.href ? "bg-surface-2 font-medium" : "text-muted"}`}>
                  {n.label}
                </Link>
              ))}
            </nav>
            <div className="mt-3 sm:hidden"><AccountMenu /></div>
          </div>
        )}
      </header>
      <main id="main" className="mx-auto w-full max-w-[1320px] flex-1 px-4 py-6 sm:px-6 sm:py-8">{children}</main>
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-[1320px] flex-col gap-2 px-4 py-5 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>For research and education only. Not investment advice. Every figure links to its source; missing figures say why.</p>
          <p className="flex gap-4">
            <Link href="/health" className="hover:text-fg">Data sources</Link>
            <Link href="/settings" className="hover:text-fg">Settings</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
