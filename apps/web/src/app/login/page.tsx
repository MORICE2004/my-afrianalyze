import type { Metadata } from "next";
import Link from "next/link";
import React from "react";
import { AuthArtwork } from "@/components/account/AuthArtwork";
import { SignInForm } from "@/components/account/SignInForm";
import { AnimatedLogo } from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AfriEdge to read source documents and keep your own portfolios.",
};

// The sign-in page stands on its own (no site header). Desktop: the form on a light panel (45%) and a dark
// panel with the brand artwork and one statement (55%). Phones: the logo and the form only; the artwork is left
// out rather than squeezed. Nothing here delays typing: the form is interactive at once.
export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const sp = await searchParams;
  const raw = Array.isArray(sp.next) ? sp.next[0] : sp.next;
  // Only a path on this site: "/x" yes, "//evil.example" or "https://..." no.
  const next = raw && /^\/(?!\/)[\w\-/?=&%.:]*$/.test(raw) ? raw : "/dashboard";
  return (
    <main id="main" className="grid min-h-dvh bg-surface lg:grid-cols-[45fr_55fr]" data-testid="login-page">
      <section className="flex flex-col px-6 pb-8 pt-[max(2rem,env(safe-area-inset-top))] sm:px-12 lg:px-16 lg:py-12">
        <Link href="/" aria-label="AfriEdge home" className="self-start"><AnimatedLogo size={30} wordClass="text-lg" /></Link>
        <div className="mx-auto w-full max-w-[25rem] py-10 lg:my-auto lg:py-12">
          <h1 className="text-[1.75rem] font-semibold leading-tight tracking-tight sm:text-[2rem]">Welcome back</h1>
          <p className="mt-2 text-[15px] leading-relaxed text-muted">
            Sign in to read source documents page by page and keep your own portfolios. Research is open to everyone.
          </p>
          <div className="mt-8"><SignInForm next={next} /></div>
        </div>
        <footer className="mx-auto flex w-full max-w-[25rem] flex-wrap gap-x-5 gap-y-2 text-xs text-muted lg:mx-0 lg:max-w-none">
          <span>© {new Date().getFullYear()} AfriEdge</span>
          <Link href="/privacy" className="hover:text-fg">Privacy</Link>
          <Link href="/cookies" className="hover:text-fg">Cookies</Link>
          <Link href="/terms" className="hover:text-fg">Terms</Link>
        </footer>
      </section>

      <aside className="relative hidden overflow-hidden bg-[#16181b] text-white lg:block" aria-label="About AfriEdge">
        <AuthArtwork />
        <div className="absolute inset-x-0 bottom-0 p-14 xl:p-20">
          <p className="max-w-xl text-[2.75rem] font-semibold leading-[1.05] tracking-tight xl:text-[3.5rem]">
            See African Markets Clearly.
          </p>
          <p className="mt-4 text-base text-white/65">Research. Value. Invest.</p>
        </div>
      </aside>
    </main>
  );
}
