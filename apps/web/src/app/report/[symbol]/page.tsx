import React from 'react';

export default async function ReportPage({ params }: { params: Promise<{ symbol: string }> }) {
  // Mock data
  const { symbol: rawSymbol } = await params;
  const symbol = rawSymbol.toUpperCase();
  const companyName = "Safaricom Plc";
  
  return (
    <div className="flex flex-col gap-10 pb-12 animate-in fade-in duration-500">
      
      {/* Company Header */}
      <div className="flex justify-between items-end border-b-2 border-black pb-5">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-5xl font-bold tracking-tighter text-black">
              {symbol}
            </h1>
            <span className="text-2xl font-serif italic text-neutral-500 mt-1">{companyName}</span>
          </div>
          <div className="flex gap-4 text-xs font-mono text-neutral-600 uppercase tracking-wider">
            <span className="bg-neutral-100 px-2 py-1">Sector: Telecom</span>
            <span className="bg-neutral-100 px-2 py-1">Exchange: NSE</span>
            <span className="bg-neutral-100 px-2 py-1">Currency: KES</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-4xl font-mono font-medium text-black tracking-tight">17.50</div>
          <div className="text-red-600 font-mono text-sm font-medium flex items-center justify-end gap-2 mt-1">
            <span className="bg-red-100 px-1 py-0.5 rounded-sm">▼ -0.45</span>
            <span>(-2.5%)</span>
          </div>
          <div className="text-xs font-mono text-neutral-500 mt-2 uppercase tracking-widest">
            Mkt Cap: <span className="text-black font-semibold">701.2B</span>
          </div>
        </div>
      </div>

      {/* Recommendation Badge (Editorial Verdict) */}
      <div className="bg-black text-white p-8 grid grid-cols-1 lg:grid-cols-4 gap-8 shadow-sm">
        <div className="lg:col-span-1 lg:border-r border-neutral-800 lg:pr-8">
          <div className="text-xs font-mono text-neutral-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
            Research Verdict
          </div>
          <div className="text-3xl font-bold text-green-400 mb-3 tracking-tight">OVERWEIGHT</div>
          <div className="text-sm text-neutral-300 leading-relaxed font-serif">
            Strong cash generation offsets regulatory overhang. Core voice decline is successfully stabilized by M-PESA growth and fixed-data penetration.
          </div>
        </div>
        <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-8 text-sm">
          <div className="space-y-3">
            <div className="font-mono text-xs uppercase tracking-widest text-neutral-500 border-b border-neutral-800 pb-2">Valuation</div>
            <p className="text-neutral-300 leading-relaxed">Trading at 11.2x P/E, a 15% discount to the 5-year historical average. Our DCF model implies a KES 22 fair value.</p>
          </div>
          <div className="space-y-3">
            <div className="font-mono text-xs uppercase tracking-widest text-neutral-500 border-b border-neutral-800 pb-2">Technical</div>
            <p className="text-neutral-300 leading-relaxed">Finding robust support at the KES 17.00 level. RSI sits at 42 (neutral). Watch for volume breakout above 18.50.</p>
          </div>
          <div className="space-y-3">
            <div className="font-mono text-xs uppercase tracking-widest text-neutral-500 border-b border-neutral-800 pb-2">Risk Factor</div>
            <p className="text-neutral-300 leading-relaxed">Ethiopia rollout execution risk and high capital intensity. Potential regulatory caps on M-PESA transactional tariffs.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
        
        {/* Financial Statements */}
        <div className="xl:col-span-7">
          <div className="flex justify-between items-end border-b-2 border-black pb-3 mb-4">
            <h2 className="font-bold text-black text-lg tracking-tight uppercase">Income Statement</h2>
            <div className="flex border border-neutral-300 text-xs font-mono">
              <button className="px-4 py-1.5 bg-black text-white font-medium">ABS</button>
              <button className="px-4 py-1.5 hover:bg-neutral-100 text-neutral-600 border-l border-neutral-300 transition-colors">%YoY</button>
              <button className="px-4 py-1.5 hover:bg-neutral-100 text-neutral-600 border-l border-neutral-300 transition-colors">MRG</button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-right font-mono">
              <thead>
                <tr className="text-neutral-500 border-b border-neutral-300 bg-[#F9F9F9]">
                  <th className="text-left font-medium py-3 px-4 w-[40%] uppercase tracking-wider text-xs">Metric (KES m)</th>
                  <th className="font-medium py-3 px-4 uppercase tracking-wider text-xs">FY22</th>
                  <th className="font-medium py-3 px-4 uppercase tracking-wider text-xs">FY23</th>
                  <th className="font-medium py-3 px-4 uppercase tracking-wider text-xs text-black">FY24</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200">
                <tr className="hover:bg-neutral-50 transition-colors">
                  <td className="text-left py-3 px-4 text-black font-medium">Service Revenue</td>
                  <td className="py-3 px-4 text-neutral-600">281,114</td>
                  <td className="py-3 px-4 text-neutral-600">295,694</td>
                  <td className="py-3 px-4 text-black font-bold bg-neutral-100/50">335,350</td>
                </tr>
                <tr className="hover:bg-neutral-50 transition-colors text-neutral-500 text-xs">
                  <td className="text-left py-2 px-4 pl-8 border-l-2 border-neutral-200">↳ M-PESA</td>
                  <td className="py-2 px-4">107,692</td>
                  <td className="py-2 px-4">117,192</td>
                  <td className="py-2 px-4 text-black bg-neutral-100/50">139,913</td>
                </tr>
                <tr className="hover:bg-neutral-50 transition-colors text-neutral-500 text-xs">
                  <td className="text-left py-2 px-4 pl-8 border-l-2 border-neutral-200">↳ Voice</td>
                  <td className="py-2 px-4">83,212</td>
                  <td className="py-2 px-4">81,050</td>
                  <td className="py-2 px-4 text-black bg-neutral-100/50">79,485</td>
                </tr>
                <tr className="hover:bg-neutral-50 transition-colors font-medium border-t-2 border-neutral-100">
                  <td className="text-left py-3 px-4 text-black">EBITDA</td>
                  <td className="py-3 px-4 text-black">149,081</td>
                  <td className="py-3 px-4 text-black">139,902</td>
                  <td className="py-3 px-4 text-black font-bold bg-neutral-100/50">148,443</td>
                </tr>
                <tr className="hover:bg-neutral-50 transition-colors text-neutral-500 text-xs">
                  <td className="text-left py-2 px-4 pl-8 border-l-2 border-neutral-200">↳ EBITDA Margin</td>
                  <td className="py-2 px-4">53.0%</td>
                  <td className="py-2 px-4">47.3%</td>
                  <td className="py-2 px-4 text-black bg-neutral-100/50">44.3%</td>
                </tr>
                <tr className="hover:bg-neutral-50 transition-colors border-t-2 border-neutral-300">
                  <td className="text-left py-3 px-4 text-black font-medium">Net Income</td>
                  <td className="py-3 px-4 text-neutral-600">67,495</td>
                  <td className="py-3 px-4 text-neutral-600">52,480</td>
                  <td className="py-3 px-4 text-black font-bold bg-neutral-100/50">42,662</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="xl:col-span-5 flex flex-col gap-10">
          
          {/* Valuation Workspace */}
          <div>
            <div className="border-b-2 border-black pb-3 mb-4">
              <h2 className="font-bold text-black text-lg tracking-tight uppercase">Valuation Engine</h2>
            </div>
            <div className="border border-neutral-200 bg-white shadow-sm p-6">
              
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="bg-black text-white text-[10px] font-mono px-2 py-1 uppercase tracking-widest">Deterministic Math</span>
                </div>
                <div className="flex items-center justify-between text-black font-mono bg-neutral-50 p-4 border border-neutral-200">
                  <div className="text-center">
                    <div className="text-neutral-500 mb-1 text-[10px] uppercase tracking-widest">Target P/B</div>
                    <div className="text-xl font-medium">3.2x</div>
                  </div>
                  <div className="text-neutral-300 text-xl">×</div>
                  <div className="text-center">
                    <div className="text-neutral-500 mb-1 text-[10px] uppercase tracking-widest">BVPS (KES)</div>
                    <div className="text-xl font-medium">6.85</div>
                  </div>
                  <div className="text-neutral-300 text-xl">=</div>
                  <div className="text-center bg-green-50 border border-green-200 px-4 py-2">
                    <div className="text-green-700 mb-1 text-[10px] uppercase tracking-widest">Fair Value</div>
                    <div className="text-xl font-bold text-green-700">21.92</div>
                  </div>
                </div>
              </div>
              
              <div className="pt-5 border-t border-neutral-200">
                <div className="flex items-center gap-2 mb-3">
                  <span className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-mono px-2 py-1 uppercase tracking-widest flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    AI Interpretation
                  </span>
                </div>
                <p className="text-neutral-700 leading-relaxed text-sm font-serif">
                  The deterministic model yields a fair value of KES 21.92, implying a <strong className="text-green-600 font-sans font-bold">+25% upside</strong>. 
                  This assumes mean-reversion to the 3-year historical P/B multiple of 3.2x. Following the intensive CapEx cycle in Ethiopia, book value growth is projected to be highly accretive over the next 12-18 months.
                </p>
              </div>
            </div>
          </div>

          {/* Evidence Lineage */}
          <div>
            <div className="border-b-2 border-black pb-3 mb-4">
              <h2 className="font-bold text-black text-lg tracking-tight uppercase">Evidence Lineage</h2>
            </div>
            <div className="border border-neutral-200 bg-white shadow-sm p-6">
              <p className="text-xs text-neutral-500 mb-5 font-mono">
                Tracing Data Point: <span className="font-bold text-black bg-neutral-100 px-1 py-0.5">FY24 M-PESA Revenue (139,913)</span>
              </p>
              
              <div className="relative pl-6 border-l-2 border-neutral-200 space-y-6">
                <div className="relative">
                  <div className="absolute -left-[29px] top-1 bg-black border-2 border-white w-3 h-3 rounded-full shadow-sm"></div>
                  <div className="text-sm font-bold text-black">Extracted Figure</div>
                  <div className="text-xs text-neutral-500 font-mono mt-1">Value: 139,913 | Confidence: 99.8%</div>
                </div>
                
                <div className="relative">
                  <div className="absolute -left-[29px] top-1 bg-white border-2 border-neutral-400 w-3 h-3 rounded-full"></div>
                  <div className="text-sm font-bold text-black">Document Parsing</div>
                  <div className="text-xs text-neutral-500 mt-1">
                    Source: <a href="#" className="text-blue-600 hover:underline hover:text-blue-800 transition-colors font-mono">Safaricom_FY24_Annual_Report.pdf</a> (Page 42, Table 3.1)
                  </div>
                </div>
                
                <div className="relative">
                  <div className="absolute -left-[29px] top-1 bg-white border-2 border-neutral-400 w-3 h-3 rounded-full"></div>
                  <div className="text-sm font-bold text-black">Exchange Connector</div>
                  <div className="text-xs text-neutral-500 mt-1 font-mono">Fetched from NSE Regulatory Filings (Timestamp: 2024-05-09 14:32:01 UTC)</div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
