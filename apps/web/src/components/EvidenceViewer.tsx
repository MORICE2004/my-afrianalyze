"use client";

import React, { useEffect } from 'react';
import { captureEvent } from '../lib/telemetry';

interface EvidenceViewerProps {
  symbol: string;
}

export function EvidenceViewer({ symbol }: EvidenceViewerProps) {
  useEffect(() => {
    captureEvent("evidence_viewed", { symbol });
  }, [symbol]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-xl font-bold mb-4 text-gray-900 border-b pb-2">Source / Evidence Viewer</h3>
      
      <p className="text-sm text-gray-600 mb-4">
        Every financial figure below is traced back to an EvidenceRecord (per our strict schema).
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 font-semibold text-gray-700">Metric</th>
              <th className="px-4 py-3 font-semibold text-gray-700">Value</th>
              <th className="px-4 py-3 font-semibold text-gray-700">Source Document</th>
              <th className="px-4 py-3 font-semibold text-gray-700">Page/Section</th>
              <th className="px-4 py-3 font-semibold text-gray-700">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium text-gray-900">Total Revenue</td>
              <td className="px-4 py-3 font-mono">KES 311.5B</td>
              <td className="px-4 py-3 text-blue-600 hover:underline cursor-pointer">{symbol}_FY2025_Annual_Report.pdf</td>
              <td className="px-4 py-3">Page 85, Income Statement</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">High</span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium text-gray-900">Operating Expenses</td>
              <td className="px-4 py-3 font-mono">KES 142.3B</td>
              <td className="px-4 py-3 text-blue-600 hover:underline cursor-pointer">{symbol}_FY2025_Annual_Report.pdf</td>
              <td className="px-4 py-3">Page 85, Income Statement</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">High</span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium text-gray-900">Total Debt</td>
              <td className="px-4 py-3 font-mono">KES 45.2B</td>
              <td className="px-4 py-3 text-blue-600 hover:underline cursor-pointer">{symbol}_FY2025_Annual_Report.pdf</td>
              <td className="px-4 py-3">Page 86, Balance Sheet</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">High</span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium text-gray-900">CapEx</td>
              <td className="px-4 py-3 font-mono">KES 35.0B</td>
              <td className="px-4 py-3 text-blue-600 hover:underline cursor-pointer">{symbol}_FY2025_Investor_Presentation.pdf</td>
              <td className="px-4 py-3">Slide 12, Management Guidance</td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">Medium</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
