'use client';
import React from 'react';
import Link from 'next/link';
import { ArrowLeft, TrendingUp, TrendingDown, Activity, Globe2, BarChart2 } from 'lucide-react';
import { AreaChart } from '@tremor/react';

export default function MarketsPage() {
  const dseData = [
    { time: '10:00', value: 2140 },
    { time: '11:00', value: 2142 },
    { time: '12:00', value: 2138 },
    { time: '13:00', value: 2145 },
    { time: '14:00', value: 2145.32 },
  ];

  const markets = [
    {
      id: 'DSE',
      name: 'Dar es Salaam Stock Exchange',
      country: 'Tanzania',
      index: 'DSEI',
      value: '2,145.32',
      change: '+1.2%',
      isPositive: true,
      volume: 'TZS 1.2B',
      chartData: dseData,
    },
    {
      id: 'NSE',
      name: 'Nairobi Securities Exchange',
      country: 'Kenya',
      index: 'NASI',
      value: '105.80',
      change: '-0.5%',
      isPositive: false,
      volume: 'KES 350M',
      chartData: dseData.map(d => ({ time: d.time, value: 106 - Math.random() * 2 })),
    },
    {
      id: 'USE',
      name: 'Uganda Securities Exchange',
      country: 'Uganda',
      index: 'ALSI',
      value: '1,023.45',
      change: '+0.1%',
      isPositive: true,
      volume: 'UGX 500M',
      chartData: dseData.map(d => ({ time: d.time, value: 1020 + Math.random() * 5 })),
    }
  ];

  const topMovers = [
    { ticker: 'CRDB', market: 'DSE', price: '540', change: '+4.5%', isPositive: true },
    { ticker: 'Safaricom', market: 'NSE', price: '15.20', change: '-2.1%', isPositive: false },
    { ticker: 'NMB', market: 'DSE', price: '4,800', change: '+1.8%', isPositive: true },
    { ticker: 'MTN', market: 'USE', price: '175', change: '+0.5%', isPositive: true },
    { ticker: 'EABL', market: 'NSE', price: '112.50', change: '-1.4%', isPositive: false },
  ];

  return (
    <div className="min-h-screen bg-[#F4F6F8] font-sans pb-12">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-gray-900 transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
              <Globe2 size={24} className="text-indigo-600" />
              Regional Markets
            </h1>
          </div>
          <div className="text-sm font-medium text-gray-500 bg-gray-100 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Markets Open
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 py-8 space-y-8">
        
        {/* Main Indices Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {markets.map((market) => (
            <div key={market.id} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden group hover:shadow-md hover:border-indigo-200 transition-all">
              <div className="p-6">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-1">{market.id}</h2>
                    <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">{market.name}</p>
                  </div>
                  <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-bold rounded-md">
                    {market.country}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-400 font-medium mb-1">{market.index}</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-gray-900">{market.value}</span>
                    </div>
                    <div className={`flex items-center gap-1 text-sm font-bold mt-1 ${market.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {market.isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      {market.change}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400 font-medium mb-1">Daily Volume</p>
                    <p className="text-lg font-bold text-gray-800">{market.volume}</p>
                  </div>
                </div>
              </div>
              
              <div className="h-24 w-full bg-gray-50 border-t border-gray-100">
                <AreaChart
                  className="h-full mt-2"
                  data={market.chartData}
                  index="time"
                  categories={['value']}
                  colors={[market.isPositive ? 'emerald' : 'rose']}
                  showXAxis={false}
                  showYAxis={false}
                  showLegend={false}
                  showGridLines={false}
                  showTooltip={false}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Analytics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Top Movers */}
          <div className="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Activity size={18} className="text-indigo-600" />
              Regional Top Movers
            </h3>
            <div className="space-y-4">
              {topMovers.map((mover, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors border border-transparent hover:border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center font-bold text-gray-600 text-xs">
                      {mover.market}
                    </div>
                    <div>
                      <div className="font-bold text-gray-900">{mover.ticker}</div>
                      <div className="text-xs text-gray-500">Local Currency</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900">{mover.price}</div>
                    <div className={`text-sm font-semibold flex items-center justify-end gap-1 ${mover.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {mover.isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      {mover.change}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Market Commentary */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
              <BarChart2 size={18} className="text-indigo-600" />
              Cross-Border Market Insight
            </h3>
            
            <div className="prose prose-sm max-w-none text-gray-600 space-y-4">
              <p className="text-base leading-relaxed">
                The <strong className="text-gray-900">Dar es Salaam Stock Exchange (DSE)</strong> continues its upward momentum, driven heavily by domestic banking sector results. CRDB and NMB have both posted record H1 profits, expanding their ROE metrics above 20%. The DSEI remains the best-performing index in the EAC year-to-date.
              </p>
              
              <div className="grid grid-cols-2 gap-4 my-6">
                <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100">
                  <div className="text-xs font-bold text-indigo-800 uppercase tracking-wider mb-2">Key Catalyst</div>
                  <div className="text-sm text-indigo-900">Foreign investor inflows returning to the DSE following dividend repatriation easing.</div>
                </div>
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                  <div className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2">Risk Factor</div>
                  <div className="text-sm text-amber-900">NSE currency depreciation (KES) dampening USD returns for foreign allocations.</div>
                </div>
              </div>
              
              <p className="text-base leading-relaxed">
                Conversely, the <strong className="text-gray-900">Nairobi Securities Exchange (NSE)</strong> is experiencing mild contraction today, largely pulled down by Safaricom and EABL. Investors are pricing in the impact of recent tax policy shifts and inflation concerns. 
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

