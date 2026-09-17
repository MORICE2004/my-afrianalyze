import React from 'react';

interface ValuationInput {
  metric: string;
  value: string;
  source: string; // e.g. "EvidenceRecord: Q3 2023 Financials"
}

interface AIValuationProps {
  methodology: string; // e.g., "Dividend Discount Model (Bank-Specific)"
  targetPrice: number;
  currentPrice: number;
  currency: string;
  inputs: ValuationInput[];
  mathTrace: string; // Step-by-step mathematical trace
}

export function AIValuations({
  methodology,
  targetPrice,
  currentPrice,
  currency,
  inputs,
  mathTrace
}: AIValuationProps) {
  const upside = ((targetPrice - currentPrice) / currentPrice) * 100;
  const isPositive = upside >= 0;

  return (
    <div className="bg-white border rounded-lg shadow-sm p-6 w-full max-w-3xl">
      <div className="border-b pb-4 mb-4 flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI Valuation Engine</h2>
          <p className="text-sm text-gray-500 mt-1">Methodology: {methodology}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Target Price</div>
          <div className="text-2xl font-bold text-gray-900">{currency} {targetPrice.toFixed(2)}</div>
          <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{upside.toFixed(2)}% Upside
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-md font-semibold text-gray-800 mb-3">Deterministic Inputs</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Evidence Source</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {inputs.map((input, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-gray-900 font-medium">{input.metric}</td>
                    <td className="px-4 py-2 text-gray-600">{input.value}</td>
                    <td className="px-4 py-2 text-gray-500 italic">{input.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-md border border-slate-200">
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Math Trace (No LLM Intermediaries)</h3>
          <pre className="text-xs text-slate-700 whitespace-pre-wrap font-mono">
            {mathTrace}
          </pre>
        </div>
      </div>
    </div>
  );
}
