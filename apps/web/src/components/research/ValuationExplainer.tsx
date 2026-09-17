import React from 'react';

interface ValuationExplainerProps {
  methodology: 'PB' | 'PE' | 'DCF';
  inputs: Record<string, number>;
  result: number;
}

export default function ValuationExplainer({ methodology, inputs, result }: ValuationExplainerProps) {
  return (
    <div className="p-4 border border-gray-300 rounded shadow-sm bg-white text-gray-800">
      <h3 className="text-lg font-bold mb-4 border-b pb-2">Valuation Model Math Chain</h3>
      {methodology === 'PB' && (
        <div className="space-y-2 font-mono text-sm">
          <div className="flex justify-between">
            <span>Book Value (BV)</span>
            <span>{inputs.bookValue.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Target P/B</span>
            <span>x {inputs.targetPB.toFixed(2)}</span>
          </div>
          <hr className="my-2 border-gray-400" />
          <div className="flex justify-between font-bold">
            <span>Target Equity Value</span>
            <span>= {(inputs.bookValue * inputs.targetPB).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Shares Outstanding</span>
            <span>/ {inputs.sharesOut.toLocaleString()}</span>
          </div>
          <hr className="my-2 border-gray-400" />
          <div className="flex justify-between font-bold text-blue-700 text-base">
            <span>Target Price</span>
            <span>= {result.toFixed(2)}</span>
          </div>
        </div>
      )}
      {/* Explicit disclaimer about deterministic nature */}
      <div className="mt-6 text-xs text-gray-500 italic">
        * Valuation is purely deterministic based on fundamental data. No AI inference is used in calculation logic.
      </div>
    </div>
  );
}
