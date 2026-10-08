import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import React from "react";
import { SignInForm } from "@/components/account/SignInForm";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AfriEdge to read source documents and keep your own portfolios.",
};

// The sign-in page stands on its own (no site header): a quiet form on the left, and on the right a dark panel
// with an architectural composition and one statement about what AfriEdge is. The geometry is drawn here in
// SVG; no third-party artwork is used.
export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const sp = await searchParams;
  const raw = Array.isArray(sp.next) ? sp.next[0] : sp.next;
  // Only a path on this site: "/x" yes, "//evil.example" or "https://..." no.
  const next = raw && /^\/(?!\/)[\w\-/?=&%.:]*$/.test(raw) ? raw : "/dashboard";
  return (
    <main id="main" className="grid min-h-screen bg-[var(--auth-ground)] lg:grid-cols-[minmax(28rem,5fr)_7fr]" data-testid="login-page">
      <section className="flex flex-col px-6 py-8 sm:px-12 lg:px-16 lg:py-12">
        <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight text-fg">
          <Image src="/logo-mark.png" alt="" width={22} height={19} priority className="dark:invert" />
          AfriEdge
        </Link>
        <div className="my-auto w-full max-w-[24rem] py-12">
          <h1 className="text-[2rem] font-semibold leading-tight tracking-tight sm:text-[2.5rem]">Sign in</h1>
          <p className="mt-3 text-[15px] leading-relaxed text-muted">
            Research on listed African companies is open to read. Sign in to read source documents page by page and to
            keep your own portfolios.
          </p>
          <div className="mt-8"><SignInForm next={next} /></div>
        </div>
        <footer className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
          <span>© AfriEdge</span>
          <Link href="/privacy" className="hover:text-fg">Privacy &amp; cookies</Link>
          <Link href="/disclaimer" className="hover:text-fg">Risk disclaimer</Link>
          <Link href="/methodology" className="hover:text-fg">Data methodology</Link>
        </footer>
      </section>

      <aside aria-hidden className="relative hidden overflow-hidden bg-[#16181b] text-white lg:block">
        <Geometry />
        <div className="absolute inset-x-0 bottom-0 p-14 xl:p-20">
          <p className="max-w-xl text-[2.6rem] font-semibold leading-[1.08] tracking-tight xl:text-[3.25rem]">
            Every figure,<br />traced to its source.
          </p>
          <p className="mt-5 max-w-md text-[15px] leading-relaxed text-white/60">
            Statements read from audited annual reports, valuations computed by fixed rules, and market data from official
            publishers across East Africa.
          </p>
        </div>
      </aside>
    </main>
  );
}

// Stacked planes seen in isometric projection, like floors of a building or layers of a balance sheet. Flat
// tones only, no glow; the one lighter face gives depth.
function Geometry() {
  const faces = [
    { d: "M520 40 L860 236 L520 432 L180 236 Z", f: "#24272b" },
    { d: "M180 236 L520 432 L520 520 L180 324 Z", f: "#1c1e21" },
    { d: "M520 432 L860 236 L860 324 L520 520 Z", f: "#d8d2c4" },
    { d: "M600 300 L860 450 L600 600 L340 450 Z", f: "#2a2d32" },
    { d: "M340 450 L600 600 L600 700 L340 550 Z", f: "#1e2023" },
    { d: "M600 600 L860 450 L860 550 L600 700 Z", f: "#353a40" },
    { d: "M300 520 L470 618 L300 716 L130 618 Z", f: "#202326" },
    { d: "M130 618 L300 716 L300 760 L130 662 Z", f: "#191b1e" },
    { d: "M300 716 L470 618 L470 662 L300 760 Z", f: "#2c3035" },
  ];
  return (
    <svg viewBox="100 0 820 780" preserveAspectRatio="xMidYMin meet" className="absolute inset-x-0 top-0 h-[64%] w-full">
      {faces.map((x, i) => <path key={i} d={x.d} fill={x.f} />)}
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <line key={i} x1={180 + i * 68} y1={236 + i * 39} x2={520 + i * 68} y2={40 + i * 39} stroke="#ffffff" strokeOpacity="0.05" />
      ))}
    </svg>
  );
}
