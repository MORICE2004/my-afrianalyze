import React from 'react';

interface EvidenceLineageProps {
  metric: string;
  value: number;
  documentContext: {
    docName: string;
    page: number;
    originalValue: string;
  };
  calculation: string;
}

export default function EvidenceLineage({ metric, value, documentContext, calculation }: EvidenceLineageProps) {
  return (
    <div className="p-4 border rounded bg-slate-50 text-gray-800 shadow-sm">
      <h3 className="font-bold text-md mb-2 pb-1 border-b border-gray-300">{metric}: Evidence Lineage</h3>
      <ul className="text-sm space-y-3 mt-4">
        <li className="flex flex-col">
          <span className="text-gray-500 uppercase text-xs font-semibold">Reported Value</span>
          <span className="font-mono text-lg">{value.toLocaleString()}</span>
        </li>
        <li className="flex flex-col">
          <span className="text-gray-500 uppercase text-xs font-semibold">Source Document</span>
          <span>{documentContext.docName} (Page {documentContext.page})</span>
        </li>
        <li className="flex flex-col">
          <span className="text-gray-500 uppercase text-xs font-semibold">Extracted Text</span>
          <span className="italic text-gray-700 bg-gray-100 p-2 rounded mt-1 border">
            "{documentContext.originalValue}"
          </span>
        </li>
        <li className="flex flex-col">
          <span className="text-gray-500 uppercase text-xs font-semibold">Calculation Chain</span>
          <code className="bg-gray-200 p-2 rounded mt-1 text-blue-800">{calculation}</code>
        </li>
      </ul>
    </div>
  );
}
