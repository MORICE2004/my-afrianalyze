"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useState } from "react";
import { SystemStatus } from "./SystemStatus";

export const NAV = [
  { href: "/", label: "Equities" },
  { href: "/markets", label: "Markets" },
  { href: "/fixed-income", label: "Fixed income" },
  { href: "/portfolio", label: "Portfolio builder" },
  { href: "/dashboard", label: "My portfolios" },
  { href: "/health", label: "Data health" },
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  // Close the mobile menu whenever the route changes (adjusting state during render, as React recommends).
  const [menuPath, setMenuPath] = useState(pathname);
  if (menuPath !== pathname) {
    setMenuPath(pathname);
    setOpen(false);
  }

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" || pathname.startsWith("/report") : pathname.startsWith(href);

  return (
    <div className="min-h-screen bg-[#F9F9F9] text-neutral-900 font-sans">
      <header className="sticky top-0 z-50 bg-white border-b border-neutral-200 shadow-sm text-sm">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 gap-4">
          <div className="flex items-center gap-8 min-w-0">
            <Link href="/" className="font-bold tracking-tight uppercase flex items-center gap-2 shrink-0">
              <span className="w-3 h-3 bg-black" aria-hidden />
              AfriAnalyze
            </Link>
            <nav aria-label="Main" className="hidden lg:flex items-center gap-5 text-neutral-600 font-medium text-xs tracking-wide uppercase">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  aria-current={isActive(n.href) ? "page" : undefined}
                  className={`pb-1 border-b-2 transition-colors ${isActive(n.href) ? "text-black border-black" : "border-transparent hover:text-black"}`}
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <SystemStatus />
            <button
              type="button"
              className="lg:hidden border border-neutral-300 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide"
              aria-expanded={open}
              aria-controls="mobile-nav"
              onClick={() => setOpen((o) => !o)}
            >
              {open ? "Close" : "Menu"}
            </button>
          </div>
        </div>
        {open && (
          <nav id="mobile-nav" aria-label="Main" className="lg:hidden border-t border-neutral-200 bg-white">
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                aria-current={isActive(n.href) ? "page" : undefined}
                className={`block px-6 py-3 text-sm border-b border-neutral-100 ${isActive(n.href) ? "font-semibold text-black" : "text-neutral-700"}`}
              >
                {n.label}
              </Link>
            ))}
          </nav>
        )}
      </header>
      <main className="mx-auto max-w-[1400px] px-4 sm:px-6 py-8">{children}</main>
      <footer className="border-t border-neutral-200 px-6 py-4 text-xs text-neutral-500">
        Research and education only. Not investment advice. Every figure links to its source; missing figures say why.
      </footer>
    </div>
  );
}
