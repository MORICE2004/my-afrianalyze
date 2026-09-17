import React from 'react';

export default function TechnicalWorkspace() {
  const regime: 'Bullish' | 'Bearish' | 'Neutral' = 'Bullish';
  
  return (
    <div className="p-4 border rounded shadow-sm bg-white">
      <div className="flex justify-between items-center mb-4 border-b pb-4">
        <h2 className="text-xl font-bold text-gray-800">Technical Analysis Workspace</h2>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500 font-semibold uppercase">Current Regime</span>
          <div className={`px-4 py-1.5 rounded text-white font-bold uppercase tracking-wider text-sm ${
            regime === 'Bullish' ? 'bg-emerald-600' : regime === 'Bearish' ? 'bg-red-600' : 'bg-gray-500'
          }`}>
            {regime}
          </div>
        </div>
      </div>
      
      {/* Charting Area Mock */}
      <div className="h-80 bg-slate-50 flex items-center justify-center border border-slate-200 text-gray-400 mb-6 rounded relative overflow-hidden">
        <div className="absolute top-2 left-2 flex space-x-2">
          <span className="px-2 py-1 bg-white border rounded text-xs font-bold text-gray-600 shadow-sm">1D</span>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 border-blue-200 border rounded text-xs font-bold shadow-sm">SMA 50</span>
          <span className="px-2 py-1 bg-purple-100 text-purple-800 border-purple-200 border rounded text-xs font-bold shadow-sm">SMA 200</span>
        </div>
        [Interactive Charting Canvas Placeholder]
      </div>
      
      {/* Indicators Grid */}
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div className="p-4 bg-gray-50 rounded border border-gray-100 shadow-sm">
          <div className="text-gray-500 mb-1 text-xs uppercase font-bold">RSI (14)</div>
          <div className="text-xl font-mono text-gray-800">65.4 <span className="text-xs text-gray-400 font-sans">Neutral</span></div>
        </div>
        <div className="p-4 bg-gray-50 rounded border border-gray-100 shadow-sm">
          <div className="text-gray-500 mb-1 text-xs uppercase font-bold">MACD (12, 26, 9)</div>
          <div className="text-lg font-bold text-emerald-600">Bullish Crossover</div>
        </div>
        <div className="p-4 bg-gray-50 rounded border border-gray-100 shadow-sm">
          <div className="text-gray-500 mb-1 text-xs uppercase font-bold">50 vs 200 SMA</div>
          <div className="text-lg font-bold text-emerald-600">Golden Cross</div>
        </div>
      </div>
    </div>
  );
}
