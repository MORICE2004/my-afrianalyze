import React from 'react';
import Link from 'next/link';

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F9F9F9] text-neutral-900 font-sans selection:bg-blue-200">
      <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-3 bg-white border-b border-neutral-200 shadow-sm text-sm">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-bold tracking-tight text-neutral-900 uppercase flex items-center gap-2">
            <img src="/logo.png" alt="AfriEdge Logo" className="h-6 w-auto" />
            AfriEdge <span className="font-light text-neutral-500">Terminal</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-neutral-600 font-medium text-xs tracking-wide uppercase">
            <Link href="/" className="hover:text-black transition-colors pb-1">Equities</Link>
            <Link href="/markets" className="hover:text-black transition-colors pb-1">Markets</Link>
            <Link href="/fixed-income" className="hover:text-black transition-colors pb-1">Fixed Income</Link>
            <Link href="/portfolio" className="hover:text-black transition-colors pb-1">Portfolios</Link>
            <Link href="/research-chat" className="hover:text-black transition-colors pb-1">Research</Link>
          </nav>
        </div>
        <div className="flex items-center gap-5">
          <div className="hidden sm:flex items-center gap-2 text-xs text-neutral-500 font-mono tracking-widest">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            SYS: ONLINE
          </div>
          <div className="w-7 h-7 bg-neutral-900 rounded-full text-white flex items-center justify-center font-bold text-xs">MR</div>
        </div>
      </header>
      <main className="mx-auto max-w-[1400px] px-6 py-8">
        {children}
      </main>
    </div>
  );
}
