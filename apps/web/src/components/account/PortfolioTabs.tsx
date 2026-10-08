"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// The two portfolio pages share one place in the navigation; this switches between them.
export function PortfolioTabs() {
  const path = usePathname();
  const tabs = [{ href: "/portfolio", label: "Builder" }, { href: "/dashboard", label: "My portfolios" }];
  return (
    <nav aria-label="Portfolio" className="mb-6 flex gap-1 border-b border-line">
      {tabs.map((t) => (
        <Link key={t.href} href={t.href} aria-current={path === t.href ? "page" : undefined}
          className={`-mb-px border-b-2 px-3 py-2 text-sm ${path === t.href ? "border-fg font-medium text-fg" : "border-transparent text-muted hover:text-fg"}`}>
          {t.label}
        </Link>
      ))}
    </nav>
  );
}
