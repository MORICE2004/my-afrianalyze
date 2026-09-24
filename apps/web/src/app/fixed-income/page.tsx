'use client';
import React from 'react';
import Link from 'next/link';
import { LineChart, BarChart } from '@tremor/react';
import { ArrowLeft, TrendingUp, Calendar, Activity } from 'lucide-react';

export default function FixedIncomePage() {
  const yieldCurveData = [
    { tenor: '35D', yield: 3.50 },
    { tenor: '91D', yield: 4.20 },
    { tenor: '182D', yield: 5.10 },
    { tenor: '364D', yield: 6.80 },
    { tenor: '2Y', yield: 8.50 },
    { tenor: '5Y', yield: 9.25 },
    { tenor: '10Y', yield: 10.50 },
    { tenor: '15Y', yield: 11.15 },
    { tenor: '20Y', yield: 12.10 },
    { tenor: '25Y', yield: 12.56 },
  ];

  const cashFlowTimeline = [
    { date: '2026-10-15', amount: 525000, type: 'Coupon', status: 'Pending' },
    { date: '2027-04-15', amount: 525000, type: 'Coupon', status: 'Pending' },
    { date: '2027-10-15', amount: 525000, type: 'Coupon', status: 'Pending' },
    { date: '2028-04-15', amount: 525000, type: 'Coupon', status: 'Pending' },
    { date: '2028-10-15', amount: 10525000, type: 'Principal + Coupon', status: 'Maturity' },
  ];

  const tBonds = [
    { tenor: '2 Years', rate: '8.50%', cleanPrice: '99.85', yieldToMaturity: '8.58%', auctionDate: '2026-10-15', issueNo: '245' },
    { tenor: '5 Years', rate: '9.25%', cleanPrice: '98.50', yieldToMaturity: '9.65%', auctionDate: '2026-10-22', issueNo: '246' },
    { tenor: '10 Years', rate: '10.50%', cleanPrice: '95.20', yieldToMaturity: '11.32%', auctionDate: '2026-11-05', issueNo: '247' },
    { tenor: '25 Years', rate: '12.56%', cleanPrice: '102.10', yieldToMaturity: '12.28%', auctionDate: '2026-12-17', issueNo: '248' },
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-12 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-gray-900 transition-colors">
              <ArrowLeft size={20} />
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Fixed Income Analytics</h1>
            <div className="h-5 w-[1px] bg-gray-300 mx-2" />
            <span className="text-sm font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md">Tanzania (TZS)</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="text-sm font-medium bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 shadow-sm transition-colors">
              Export Curve Data
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 py-8 space-y-8">
        
        {/* Top Analytics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Yield Curve Chart */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <Activity size={18} className="text-blue-600" />
                  Sovereign Yield Curve
                </h2>
                <p className="text-sm text-gray-500 mt-1">Normal upward sloping curve indicating economic expansion</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase font-semibold">2Y-10Y Spread</div>
                <div className="text-xl font-bold text-green-600">+200 bps</div>
              </div>
            </div>
            
            <LineChart
              className="h-72"
              data={yieldCurveData}
              index="tenor"
              categories={['yield']}
              colors={['blue']}
              valueFormatter={(val) => `${val.toFixed(2)}%`}
              yAxisWidth={40}
              showLegend={false}
              curveType="natural"
            />
          </div>

          {/* Key Rates Summary */}
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-blue-300 transition-colors cursor-default group">
              <div className="text-sm font-medium text-gray-500 mb-2">Central Bank Rate (CBR)</div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-gray-900">6.00%</span>
                <span className="text-sm font-medium text-gray-400 group-hover:text-blue-600 transition-colors">Maintained</span>
              </div>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-blue-300 transition-colors cursor-default">
              <div className="text-sm font-medium text-gray-500 mb-2">Inflation Rate (Headline)</div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-gray-900">3.20%</span>
                <span className="text-sm font-medium text-red-500">↑ 10bps</span>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-900 to-indigo-900 rounded-xl shadow-sm p-6 text-white relative overflow-hidden">
              <TrendingUp className="absolute right-[-10px] bottom-[-10px] w-32 h-32 text-white/10" />
              <div className="relative z-10">
                <div className="text-blue-100 text-sm font-medium mb-1">Real Yield (10Y)</div>
                <div className="text-4xl font-bold mb-2">7.30%</div>
                <p className="text-xs text-blue-200 leading-relaxed">
                  Tanzanian 10Y bonds currently offer highly attractive real yields compared to regional peers (Kenya: 4.5%, Uganda: 6.2%).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bond Analysis & Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Active Issues Table */}
          <div className="lg:col-span-8 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-gray-900">Benchmark Treasury Bonds</h2>
              <button className="text-sm text-blue-600 font-medium hover:underline">View All Issues</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50/80 border-b border-gray-200">
                    <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">Tenor / Issue</th>
                    <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Coupon</th>
                    <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Clean Price</th>
                    <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">YTM</th>
                    <th className="py-3 px-6 text-xs font-semibold text-gray-500 uppercase tracking-wider text-right">Next Auction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {tBonds.map((bond, idx) => (
                    <tr key={idx} className="hover:bg-blue-50/50 transition-colors cursor-pointer group">
                      <td className="py-4 px-6">
                        <div className="font-bold text-gray-900 group-hover:text-blue-700">{bond.tenor}</div>
                        <div className="text-xs text-gray-500">Issue #{bond.issueNo}</div>
                      </td>
                      <td className="py-4 px-6 text-right font-medium text-gray-900">{bond.rate}</td>
                      <td className="py-4 px-6 text-right text-gray-600">{bond.cleanPrice}</td>
                      <td className="py-4 px-6 text-right font-bold text-indigo-600">{bond.yieldToMaturity}</td>
                      <td className="py-4 px-6 text-right text-sm text-gray-500">{bond.auctionDate}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cash-flow Timeline Widget */}
          <div className="lg:col-span-4 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Calendar size={18} className="text-amber-500" />
                Cash-Flow Timeline
              </h2>
              <p className="text-xs text-gray-500 mt-1">Simulated for TZS 10M in 10.50% 10Y Bond</p>
            </div>
            
            <div className="p-6 flex-1 overflow-y-auto">
              <div className="relative pl-6 border-l-2 border-gray-100 space-y-6">
                {cashFlowTimeline.map((cf, idx) => (
                  <div key={idx} className="relative">
                    <div className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 border-white shadow-sm ${cf.status === 'Maturity' ? 'bg-indigo-500' : 'bg-blue-400'}`}></div>
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                      <div className="flex justify-between items-start mb-1">
                        <div className="font-semibold text-sm text-gray-900">{cf.date}</div>
                        <div className={`text-xs font-bold px-2 py-0.5 rounded ${cf.status === 'Maturity' ? 'bg-indigo-100 text-indigo-700' : 'bg-blue-50 text-blue-700'}`}>
                          {cf.type}
                        </div>
                      </div>
                      <div className="text-xl font-bold text-gray-900 flex items-center gap-1 mt-2">
                        <span className="text-sm font-normal text-gray-400">TZS</span>
                        {cf.amount.toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

