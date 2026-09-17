'use client';
import React, { useState } from 'react';

export default function FinancialStatements() {
  const [showYoY, setShowYoY] = useState(false);
  const [activeStmt, setActiveStmt] = useState<'IS' | 'BS' | 'CF'>('IS');

  return (
    <div className="p-4 bg-white border rounded shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <div className="space-x-4">
          <button 
            className={`font-bold px-3 py-1 rounded ${activeStmt === 'IS' ? 'bg-blue-100 text-blue-800' : 'text-gray-500 hover:bg-gray-100'}`} 
            onClick={() => setActiveStmt('IS')}
          >
            Income Statement
          </button>
          <button 
            className={`font-bold px-3 py-1 rounded ${activeStmt === 'BS' ? 'bg-blue-100 text-blue-800' : 'text-gray-500 hover:bg-gray-100'}`} 
            onClick={() => setActiveStmt('BS')}
          >
            Balance Sheet
          </button>
          <button 
            className={`font-bold px-3 py-1 rounded ${activeStmt === 'CF' ? 'bg-blue-100 text-blue-800' : 'text-gray-500 hover:bg-gray-100'}`} 
            onClick={() => setActiveStmt('CF')}
          >
            Cash Flow
          </button>
        </div>
        <label className="flex items-center space-x-2 text-sm font-semibold text-gray-700 cursor-pointer bg-gray-50 p-2 rounded border">
          <input 
            type="checkbox" 
            checked={showYoY} 
            onChange={(e) => setShowYoY(e.target.checked)} 
            className="rounded"
          />
          <span>Show YoY Growth</span>
        </label>
      </div>
      
      <div className="overflow-x-auto border rounded border-gray-300">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-slate-100 text-gray-700 font-semibold border-b">
            <tr>
              <th className="p-3 border-r">Line Item (Millions)</th>
              <th className="p-3 text-right">FY21</th>
              {showYoY && <th className="p-3 text-right text-gray-500 text-xs">YoY %</th>}
              <th className="p-3 text-right">FY22</th>
              {showYoY && <th className="p-3 text-right text-gray-500 text-xs">YoY %</th>}
              <th className="p-3 text-right">FY23</th>
              {showYoY && <th className="p-3 text-right text-gray-500 text-xs">YoY %</th>}
            </tr>
          </thead>
          <tbody className="font-mono">
            {activeStmt === 'IS' && (
              <>
                <tr className="border-b hover:bg-slate-50">
                  <td className="p-3 border-r text-gray-800">Gross Revenue</td>
                  <td className="p-3 text-right">950.00</td>
                  {showYoY && <td className="p-3 text-right text-green-600">+5.2%</td>}
                  <td className="p-3 text-right">1,000.00</td>
                  {showYoY && <td className="p-3 text-right text-green-600">+10.0%</td>}
                  <td className="p-3 text-right">1,100.00</td>
                  {showYoY && <td className="p-3 text-right text-gray-400">-</td>}
                </tr>
                <tr className="border-b hover:bg-slate-50">
                  <td className="p-3 border-r text-gray-800">Cost of Revenue</td>
                  <td className="p-3 text-right">(400.00)</td>
                  {showYoY && <td className="p-3 text-right text-red-600">+12.5%</td>}
                  <td className="p-3 text-right">(450.00)</td>
                  {showYoY && <td className="p-3 text-right text-red-600">+6.6%</td>}
                  <td className="p-3 text-right">(480.00)</td>
                  {showYoY && <td className="p-3 text-right text-gray-400">-</td>}
                </tr>
                <tr className="border-b font-bold bg-gray-50">
                  <td className="p-3 border-r text-gray-900">Gross Profit</td>
                  <td className="p-3 text-right">550.00</td>
                  {showYoY && <td className="p-3 text-right">--</td>}
                  <td className="p-3 text-right">550.00</td>
                  {showYoY && <td className="p-3 text-right text-green-600">+12.7%</td>}
                  <td className="p-3 text-right">620.00</td>
                  {showYoY && <td className="p-3 text-right text-gray-400">-</td>}
                </tr>
              </>
            )}
            {activeStmt !== 'IS' && (
              <tr>
                <td colSpan={7} className="p-6 text-center text-gray-500 italic">
                  Data structure mocked for {activeStmt}. Refer to Income Statement for YoY toggle demonstration.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
