import React from 'react';
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh]">
      <div className="w-full max-w-3xl">
        <h1 className="text-4xl font-light tracking-tight text-neutral-900 mb-10 text-center">
          African Equity <span className="font-semibold font-serif italic">Intelligence</span>
        </h1>
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-neutral-400 group-focus-within:text-black transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            className="block w-full pl-12 pr-4 py-5 border border-neutral-300 bg-white text-xl shadow-sm focus:ring-1 focus:ring-black focus:border-black font-mono placeholder-neutral-400 rounded-none transition-shadow hover:shadow-md outline-none"
            placeholder="Search companies, symbols, or macro themes..."
            autoFocus
          />
          <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
             <kbd className="hidden sm:inline-flex items-center gap-1 border border-neutral-200 px-2 py-1 text-xs font-sans font-medium text-neutral-400 bg-neutral-50 rounded-sm">
                <span className="text-[10px]">Press</span> ↵
             </kbd>
          </div>
        </div>
        <div className="mt-8 flex justify-center items-center gap-6 text-sm font-mono text-neutral-500">
          <span className="uppercase text-[10px] tracking-widest text-neutral-400 font-bold bg-neutral-100 px-2 py-1">Trending</span>
          <Link href="/report/SFA" className="text-neutral-700 hover:text-black hover:underline underline-offset-4 decoration-neutral-300 transition-all">SFA.KE</Link>
          <Link href="/report/EQTY" className="text-neutral-700 hover:text-black hover:underline underline-offset-4 decoration-neutral-300 transition-all">EQTY.KE</Link>
          <Link href="/report/MTNN" className="text-neutral-700 hover:text-black hover:underline underline-offset-4 decoration-neutral-300 transition-all">MTNN.NG</Link>
          <Link href="/report/CRDB" className="text-neutral-700 hover:text-black hover:underline underline-offset-4 decoration-neutral-300 transition-all">CRDB.TZ</Link>
        </div>
      </div>
    </div>
  );
}
