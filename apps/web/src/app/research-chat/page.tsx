'use client';

import React, { useState } from 'react';
import { Search, Info, FileText, TrendingUp, AlertCircle, ChevronRight, Bookmark } from 'lucide-react';
import Link from 'next/link';

export default function ResearchCopilot() {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSubmittedQuery(query);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      {/* Copilot Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="font-bold text-xl tracking-tight text-gray-900">
              AfriAnalyze
            </Link>
            <div className="h-6 w-[1px] bg-gray-300" />
            <div className="flex items-center gap-2 text-indigo-600 bg-indigo-50 px-3 py-1.5 rounded-full text-sm font-semibold">
              <Info size={16} />
              <span>Research Copilot</span>
            </div>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span>Context: NMB Bank Plc (DSE: NMB)</span>
            </div>
            <div className="flex items-center gap-2">
              <FileText size={16} />
              <span>Data As Of: Q2 2026</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-[1600px] w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 p-6">
        
        {/* Left Sidebar: Context & Sources */}
        <aside className="lg:col-span-3 space-y-6 hidden lg:block">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Bookmark size={18} className="text-gray-400" />
              Active Context
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Target Entity</div>
                <div className="font-semibold text-gray-900">NMB Bank Plc</div>
                <div className="text-sm text-gray-600">Commercial Banking • Tanzania</div>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Active Documents</div>
                <ul className="space-y-2 mt-2">
                  <li className="flex items-center gap-2 text-sm text-indigo-600 hover:underline cursor-pointer">
                    <FileText size={14} /> NMB_Q2_2026_Financials.pdf
                  </li>
                  <li className="flex items-center gap-2 text-sm text-indigo-600 hover:underline cursor-pointer">
                    <FileText size={14} /> BOT_Banking_Sector_Report.pdf
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp size={18} className="text-gray-400" />
              Quick Queries
            </h3>
            <div className="space-y-2">
              {[
                "Analyze NMB's Net Interest Margin trend",
                "Compare NMB vs CRDB on Cost-to-Income",
                "What is the impact of BOT reserve requirements?",
                "Extract NMB's Non-Performing Loans ratio"
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(q)}
                  className="w-full text-left p-3 text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-transparent hover:border-gray-200 transition-colors flex items-center justify-between group"
                >
                  <span className="truncate pr-2">{q}</span>
                  <ChevronRight size={14} className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content: AI Copilot Interface */}
        <main className="lg:col-span-9 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-[calc(100vh-120px)]">
          
          {/* Scrollable Output Area */}
          <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-gray-50/50">
            {submittedQuery ? (
              <>
                <div className="flex gap-4 max-w-4xl">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-indigo-600 font-bold text-sm">U</span>
                  </div>
                  <div className="text-lg text-gray-900 font-medium pt-1">
                    {submittedQuery}
                  </div>
                </div>

                <div className="flex gap-4 max-w-5xl">
                  <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0 mt-1 shadow-md">
                    <span className="text-white font-bold text-sm">A</span>
                  </div>
                  <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 text-gray-800 leading-relaxed space-y-4">
                    <p>
                      Based on the <span className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-sm font-medium border border-blue-100 cursor-pointer hover:bg-blue-100"><FileText size={12}/> Q2 2026 Financials</span>, NMB Bank's Net Interest Margin (NIM) has expanded to <strong>11.4%</strong>, up from 10.8% in Q2 2025.
                    </p>
                    <p>
                      This expansion is primarily driven by:
                    </p>
                    <ul className="list-disc pl-5 space-y-2">
                      <li>
                        A strategic shift towards high-yield retail lending, which now constitutes 62% of the loan book <sup className="text-indigo-600 font-bold cursor-pointer hover:underline">[1]</sup>.
                      </li>
                      <li>
                        A sustained low cost of funds at 2.8%, bolstered by a strong CASA (Current and Savings Accounts) ratio of 74% <sup className="text-indigo-600 font-bold cursor-pointer hover:underline">[2]</sup>.
                      </li>
                    </ul>
                    
                    <div className="mt-6 pt-4 border-t border-gray-100">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Evidence Citations</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm">
                          <div className="text-indigo-600 font-medium mb-1">[1] NMB_Q2_2026_Financials.pdf</div>
                          <div className="text-gray-600 text-xs">Page 14, Management Discussion: "Retail lending grew by 18% y/y, driving yield on advances up by 40bps..."</div>
                        </div>
                        <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm">
                          <div className="text-indigo-600 font-medium mb-1">[2] NMB_Q2_2026_Financials.pdf</div>
                          <div className="text-gray-600 text-xs">Page 22, Funding Mix: "CASA deposits reached TZS 6.2 Trillion, representing 74% of total deposits..."</div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-3 rounded-lg border border-amber-100">
                      <AlertCircle size={16} className="flex-shrink-0" />
                      <p><strong>Note:</strong> The BOT recently increased the statutory minimum reserve (SMR) requirement, which may compress margins slightly in H2 2026.</p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto space-y-6">
                <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center shadow-inner">
                  <Search className="w-8 h-8 text-gray-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Research Copilot</h2>
                  <p className="text-gray-500">
                    Ask analytical questions about NMB Bank Plc. All responses are derived directly from the connected context and cited inline.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-gray-200">
            <form onSubmit={handleSearch} className="max-w-4xl mx-auto relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about margins, asset quality, valuation metrics..."
                className="w-full bg-gray-50 border border-gray-300 rounded-xl py-4 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm text-gray-900 text-lg transition-all"
              />
              <button
                type="submit"
                disabled={!query.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={20} />
              </button>
            </form>
            <div className="text-center mt-2 text-xs text-gray-400">
              Copilot uses retrieval-augmented generation on vetted financial reports. It does not provide financial advice.
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
