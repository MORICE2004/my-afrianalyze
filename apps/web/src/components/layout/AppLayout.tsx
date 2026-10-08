"use client";

import * as Dropdown from "@radix-ui/react-dropdown-menu";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React, { useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { CommandPalette } from "@/components/CommandPalette";
import { CookieConsent } from "@/components/CookieConsent";
import { SecuritySearch } from "@/components/SecuritySearch";
import { ToastProvider } from "@/components/ui/Toast";
import { refreshAccount, useAccount } from "@/lib/account";
import { ThemeToggle } from "./ThemeToggle";

// One primary navigation. The logo goes home; secondary pages sit in "More"; legal pages live in the footer only.
export const NAV = [
  { href: "/markets", label: "Markets", match: (p: string) => p.startsWith("/markets") },
  { href: "/research", label: "Research", match: (p: string) => p.startsWith("/research") || p.startsWith("/report") || p.startsWith("/sources") },
  { href: "/portfolio", label: "Portfolio", match: (p: string) => p.startsWith("/portfolio") || p.startsWith("/dashboard") },
  { href: "/news", label: "News", match: (p: string) => p.startsWith("/news") },
  { href: "/health", label: "Data sources", match: (p: string) => p.startsWith("/health") },
];
export const MORE = [
  { href: "/fixed-income", label: "Fixed income" },
  { href: "/funds", label: "Unit trusts" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/settings", label: "Settings" },
];
// Footer: short columns of secondary links. The main navigation is not repeated here.
const FOOTER: { title: string; links: [string, string][] }[] = [
  { title: "Product", links: [["/fixed-income", "Fixed income"], ["/funds", "Unit trusts"], ["/watchlist", "Watchlist"]] },
  { title: "Company", links: [["/about", "About"], ["/methodology", "Data methodology"], ["/health", "Data sources"]] },
  { title: "Legal", links: [["/disclaimer", "Risk disclaimer"], ["/privacy", "Privacy policy"], ["/cookies", "Cookie policy"], ["/terms", "Terms of use"]] },
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
  // The sign-in page is a full-screen composition of its own.
  if (pathname === "/login") return <ToastProvider>{children}<CookieConsent /></ToastProvider>;

  return (
    <ToastProvider>
    <CommandPalette />
    <CookieConsent />
    <div className="flex min-h-screen flex-col bg-background text-fg">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded focus:bg-surface focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/85">
        <div className="mx-auto flex min-h-14 max-w-[1320px] flex-wrap items-center gap-x-3 gap-y-2 px-4 py-2 sm:px-6">
          <Link href="/" aria-label="AfriEdge home" className="flex shrink-0 items-center" data-testid="header-logo">
            <Logo size={22} />
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
            <button type="button" onClick={() => window.dispatchEvent(new Event("afriedge:palette"))} data-testid="palette-open"
              className="hidden h-9 items-center gap-1.5 rounded-md border border-line px-2.5 text-xs text-muted transition-colors hover:text-fg xl:inline-flex"
              aria-label="Quick search (Ctrl+K)">
              <kbd className="font-sans">Ctrl K</kbd>
            </button>
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
      <footer className="border-t border-line bg-surface" data-testid="site-footer">
        <div className="mx-auto max-w-[1320px] px-4 pb-6 pt-10 sm:px-6">
          <div className="grid gap-10 md:grid-cols-[minmax(0,1.2fr)_minmax(0,2fr)]">
            <div className="max-w-sm">
              <Link href="/" aria-label="AfriEdge home" className="inline-flex"><Logo size={24} wordClass="text-base" /></Link>
              <p className="mt-3 text-sm font-medium text-fg">African Financial Intelligence</p>
              <p className="mt-1 text-sm leading-relaxed text-muted">Research on listed African companies, with every figure traced to its source.</p>
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-3">
              {FOOTER.map((col) => (
                <nav key={col.title} aria-label={col.title} className="min-w-0 break-words">
                  <h2 className="text-xs font-semibold text-fg">{col.title}</h2>
                  <ul className="mt-3 space-y-2 text-sm">
                    {col.links.map(([h, l]) => <li key={h}><Link href={h} className="text-muted transition-colors hover:text-fg">{l}</Link></li>)}
                  </ul>
                </nav>
              ))}
            </div>
          </div>
          <div className="mt-10 flex flex-col gap-3 border-t border-line pt-5 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
            <p>© {new Date().getFullYear()} AfriEdge. For research and education; not investment advice.</p>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <Link href="/privacy" className="hover:text-fg">Privacy</Link>
              <Link href="/terms" className="hover:text-fg">Terms</Link>
              <button type="button" onClick={() => window.dispatchEvent(new Event("afriedge:cookie-preferences"))}
                className="hover:text-fg" data-testid="footer-cookie-preferences">Cookie preferences</button>
            </div>
          </div>
        </div>
      </footer>
    </div>
    </ToastProvider>
  );
}
