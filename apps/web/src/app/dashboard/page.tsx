"use client";

import React, { useState, useEffect } from 'react';

// Mock types corresponding to the backend Pydantic models
interface Asset {
  ticker: string;
  targetWeight: number;
  currentWeight: number;
  drift: number;
  currency: string;
}

interface SavedPortfolio {
  id: string;
  name: string;
  totalValue: number;
  pl: number; // Total P&L
  baseCurrency: string;
  assets: Asset[];
}

export default function DashboardPage() {
  const [portfolios, setPortfolios] = useState<SavedPortfolio[]>([]);

  useEffect(() => {
    // In a real application, this would fetch from a protected API route
    // Here we use mock data representing a user's saved portfolios
    const mockData: SavedPortfolio[] = [
      {
        id: "1",
        name: "African Tech Growth",
        totalValue: 50000,
        pl: 4500,
        baseCurrency: "USD",
        assets: [
          { ticker: "MTNN.LG", targetWeight: 0.4, currentWeight: 0.46, drift: 0.06, currency: "NGN" },
          { ticker: "SCOM.NR", targetWeight: 0.6, currentWeight: 0.54, drift: -0.06, currency: "KES" }
        ]
      },
      {
        id: "2",
        name: "Pan-African Banks",
        totalValue: 120000,
        pl: -1200,
        baseCurrency: "ZAR",
        assets: [
          { ticker: "EQTY.NR", targetWeight: 0.5, currentWeight: 0.49, drift: -0.01, currency: "KES" },
          { ticker: "STANBIC.LG", targetWeight: 0.5, currentWeight: 0.51, drift: 0.01, currency: "NGN" }
        ]
      }
    ];
    
    setPortfolios(mockData);
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-end mb-8 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Portfolio Dashboard</h1>
          <p className="text-gray-500 mt-1">Multi-Currency Performance & Rebalance Alerts</p>
        </div>
      </div>
      
      {portfolios.length === 0 ? (
        <p className="text-gray-500">No portfolios found. Create one to get started.</p>
      ) : (
        portfolios.map(portfolio => {
          const needsRebalance = portfolio.assets.some(a => Math.abs(a.drift) >= 0.05);

          return (
            <div key={portfolio.id} className="border border-gray-200 bg-white p-6 rounded-xl shadow-sm mb-8 relative">
              {needsRebalance && (
                <div className="absolute top-0 right-0 -mt-3 -mr-3 bg-red-100 text-red-800 text-xs font-bold px-3 py-1 rounded-full shadow-md border border-red-200">
                  ⚠️ Action Required
                </div>
              )}
              
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">{portfolio.name}</h2>
                  <p className="text-sm text-gray-500">Base Currency: <span className="font-semibold text-gray-700">{portfolio.baseCurrency}</span></p>
                </div>
                <div className="text-right bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <p className="text-xs text-gray-500 uppercase font-semibold">Total Value ({portfolio.baseCurrency})</p>
                  <p className="text-2xl font-bold text-gray-900">{portfolio.totalValue.toLocaleString()}</p>
                  <p className={`text-sm font-bold ${portfolio.pl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {portfolio.pl >= 0 ? '+' : ''}{portfolio.pl.toLocaleString()} P&L
                  </p>
                </div>
              </div>
              
              <h3 className="text-sm font-semibold mb-3 text-gray-700 uppercase tracking-wider">Asset Allocation & Drift</h3>
              <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="min-w-full text-sm text-left text-gray-700">
                  <thead className="text-xs text-gray-600 uppercase bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3">Ticker</th>
                      <th scope="col" className="px-6 py-3">Local Ccy</th>
                      <th scope="col" className="px-6 py-3 text-right">Target</th>
                      <th scope="col" className="px-6 py-3 text-right">Current</th>
                      <th scope="col" className="px-6 py-3 text-right">Drift</th>
                      <th scope="col" className="px-6 py-3 text-center">Alerts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {portfolio.assets.map(asset => {
                      const isDriftHigh = Math.abs(asset.drift) >= 0.05;
                      return (
                        <tr key={asset.ticker} className={`bg-white hover:bg-gray-50 ${isDriftHigh ? 'bg-red-50/20' : ''}`}>
                          <td className="px-6 py-4 font-bold text-gray-900 whitespace-nowrap">
                            {asset.ticker}
                          </td>
                          <td className="px-6 py-4 font-medium text-gray-500">
                            {asset.currency}
                          </td>
                          <td className="px-6 py-4 text-right font-medium">
                            {(asset.targetWeight * 100).toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 text-right font-medium">
                            {(asset.currentWeight * 100).toFixed(1)}%
                          </td>
                          <td className={`px-6 py-4 text-right font-bold ${isDriftHigh ? 'text-red-600' : 'text-gray-900'}`}>
                            {asset.drift > 0 ? '+' : ''}{(asset.drift * 100).toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 text-center">
                            {isDriftHigh ? (
                              <span className="inline-flex items-center gap-1 bg-red-100 text-red-800 text-xs font-bold px-2.5 py-1 rounded border border-red-200">
                                <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
                                Rebalance
                              </span>
                            ) : (
                              <span className="bg-green-50 text-green-700 text-xs font-medium px-2.5 py-1 rounded border border-green-200">
                                Optimal
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
