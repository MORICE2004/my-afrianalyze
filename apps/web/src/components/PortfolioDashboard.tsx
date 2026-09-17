'use client';

import React, { useState } from 'react';
import { Card, Title, Text, Metric, Flex, Grid, BarList, BarChart } from '@tremor/react';

const portfolios = [
  {
    id: 'A',
    name: 'Portfolio A (Balanced Growth)',
    expectedReturn: '12.5%',
    volatility: '8.2%',
    yield: '6.8%',
    allocations: [
      { name: 'Financials', value: 40 },
      { name: 'Telecom', value: 25 },
      { name: 'Manufacturing', value: 15 },
      { name: 'Government Bonds', value: 20 },
    ],
    currency: [
      { name: 'TZS', value: 70 },
      { name: 'KES', value: 20 },
      { name: 'USD', value: 10 },
    ]
  },
  {
    id: 'B',
    name: 'Portfolio B (High Yield Income)',
    expectedReturn: '10.2%',
    volatility: '5.4%',
    yield: '9.5%',
    allocations: [
      { name: 'Financials', value: 30 },
      { name: 'Government Bonds', value: 60 },
      { name: 'Corporate Bonds', value: 10 },
    ],
    currency: [
      { name: 'TZS', value: 90 },
      { name: 'USD', value: 10 },
    ]
  },
  {
    id: 'C',
    name: 'Portfolio C (Aggressive Equity)',
    expectedReturn: '16.8%',
    volatility: '14.5%',
    yield: '4.2%',
    allocations: [
      { name: 'Telecom', value: 45 },
      { name: 'Financials', value: 35 },
      { name: 'Consumer Goods', value: 20 },
    ],
    currency: [
      { name: 'TZS', value: 60 },
      { name: 'KES', value: 30 },
      { name: 'UGX', value: 10 },
    ]
  }
];

export default function PortfolioDashboard({ formData }: { formData: any }) {
  const [selectedPortfolio, setSelectedPortfolio] = useState(portfolios[0]);

  return (
    <div className="space-y-8">
      {/* Portfolio Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {portfolios.map((p) => (
          <button
            key={p.id}
            onClick={() => setSelectedPortfolio(p)}
            className={`p-6 rounded-2xl text-left transition-all duration-300 border-2 ${
              selectedPortfolio.id === p.id
                ? 'border-black bg-black text-white shadow-xl transform scale-[1.02]'
                : 'border-transparent bg-white shadow-sm hover:shadow-md hover:border-gray-200 text-gray-900'
            }`}
          >
            <h3 className="font-semibold text-lg mb-4">{p.name}</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className={`text-sm ${selectedPortfolio.id === p.id ? 'text-gray-400' : 'text-gray-500'}`}>Exp. Return</span>
                <span className="font-bold">{p.expectedReturn}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className={`text-sm ${selectedPortfolio.id === p.id ? 'text-gray-400' : 'text-gray-500'}`}>Est. Volatility</span>
                <span className="font-bold">{p.volatility}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className={`text-sm ${selectedPortfolio.id === p.id ? 'text-gray-400' : 'text-gray-500'}`}>Div. Yield</span>
                <span className="font-bold">{p.yield}</span>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Sector Concentration */}
        <Card className="rounded-2xl border-none shadow-sm ring-1 ring-gray-100">
          <Title className="text-gray-900 font-semibold mb-6">Sector Concentration (Risk Exposure)</Title>
          <BarList 
            data={selectedPortfolio.allocations} 
            className="mt-2"
            color="indigo"
          />
        </Card>

        {/* Currency Exposure */}
        <Card className="rounded-2xl border-none shadow-sm ring-1 ring-gray-100">
          <Title className="text-gray-900 font-semibold mb-6">Currency Exposure</Title>
          <BarChart
            className="h-72 mt-4"
            data={selectedPortfolio.currency}
            index="name"
            categories={['value']}
            colors={['emerald']}
            valueFormatter={(number: number) => `${number}%`}
            yAxisWidth={48}
            showLegend={false}
          />
        </Card>
      </div>

      <Card className="rounded-2xl border-none shadow-sm ring-1 ring-gray-100">
        <Title className="text-gray-900 font-semibold mb-2">Simulated Stress Test</Title>
        <Text>Estimated impact of regional market shocks on {selectedPortfolio.name}</Text>
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">Currency Devaluation (-10%)</div>
            <div className="text-xl font-bold text-red-600">-{(parseFloat(selectedPortfolio.volatility) * 1.2).toFixed(1)}%</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">Interest Rate Hike (+200bps)</div>
            <div className="text-xl font-bold text-red-600">-{(parseFloat(selectedPortfolio.volatility) * 0.8).toFixed(1)}%</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">Telecom Sector Slump</div>
            <div className="text-xl font-bold text-red-600">-{(selectedPortfolio.allocations.find(a => a.name === 'Telecom')?.value || 0) * 0.15}%</div>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
            <div className="text-sm text-gray-500 mb-1">Financials Rally</div>
            <div className="text-xl font-bold text-green-600">+{(selectedPortfolio.allocations.find(a => a.name === 'Financials')?.value || 0) * 0.2}%</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
