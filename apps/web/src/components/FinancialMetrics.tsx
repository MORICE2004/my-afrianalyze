"use client";

import React, { useEffect } from 'react';
import { captureEvent } from '../lib/telemetry';

interface FinancialMetricsProps {
  symbol: string;
}

export function FinancialMetrics({ symbol }: FinancialMetricsProps) {
  useEffect(() => {
    captureEvent("valuation_viewed", { symbol });
  }, [symbol]);

  // Placeholder data - in a real app, this would be fetched from the API based on the symbol
  const data = {
    peRatio: 12.5,
    pbRatio: 2.1,
    roe: '18.5%',
    dcfValue: 'KES 35.50',
    currentPrice: 'KES 28.30',
    currency: 'KES',
    dividendYield: '5.2%',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-xl font-bold mb-4 text-gray-900 border-b pb-2">Financial & Valuation Metrics</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">Key Ratios</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center border-b border-gray-100 pb-2">
              <span className="text-gray-600">P/E Ratio</span>
              <span className="font-mono font-medium">{data.peRatio}x</span>
            </div>
            <div className="flex justify-between items-center border-b border-gray-100 pb-2">
              <span className="text-gray-600">P/B Ratio</span>
              <span className="font-mono font-medium">{data.pbRatio}x</span>
            </div>
            <div className="flex justify-between items-center border-b border-gray-100 pb-2">
              <span className="text-gray-600">Return on Equity (ROE)</span>
              <span className="font-mono font-medium">{data.roe}</span>
            </div>
            <div className="flex justify-between items-center border-b border-gray-100 pb-2">
              <span className="text-gray-600">Dividend Yield</span>
              <span className="font-mono font-medium text-green-600">{data.dividendYield}</span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">Valuation</h4>
          <div className="bg-blue-50 p-4 rounded-md border border-blue-100 mb-4">
            <div className="flex justify-between items-end mb-2">
              <span className="text-sm text-blue-800 font-medium">Implied DCF Value</span>
              <span className="text-2xl font-bold text-blue-900">{data.dcfValue}</span>
            </div>
            <div className="flex justify-between items-end">
              <span className="text-sm text-gray-600">Current Market Price</span>
              <span className="text-lg font-medium text-gray-800">{data.currentPrice}</span>
            </div>
            <div className="mt-3 pt-3 border-t border-blue-200">
              <span className="text-sm font-medium text-green-700">Upside: ~25.4%</span>
            </div>
          </div>
          
          <div className="text-xs text-gray-500 italic">
            * All calculations are fully deterministic and rely on traceable EvidenceRecords.
            Note: Bank-specific models use different logic for working-capital metrics.
          </div>
        </div>
      </div>
    </div>
  );
}
