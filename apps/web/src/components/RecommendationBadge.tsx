import React from 'react';

type RecommendationType = 'BUY' | 'SELL' | 'HOLD';

interface RecommendationBadgeProps {
  recommendation: RecommendationType;
  confidence: number;
  rationale: string;
}

export function RecommendationBadge({ recommendation, confidence, rationale }: RecommendationBadgeProps) {
  const colors = {
    BUY: 'bg-green-100 text-green-800 border-green-200',
    SELL: 'bg-red-100 text-red-800 border-red-200',
    HOLD: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  };

  return (
    <div className="flex flex-col gap-2 p-4 border rounded-lg bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Deterministic Recommendation</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-bold border ${colors[recommendation]}`}>
          {recommendation}
        </span>
      </div>
      
      <div className="flex items-center gap-2 mt-2">
        <div className="text-sm text-gray-600">Confidence Score:</div>
        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-600 rounded-full" 
            style={{ width: `${Math.min(100, Math.max(0, confidence * 100))}%` }}
          />
        </div>
        <div className="text-sm font-medium text-gray-900">{(confidence * 100).toFixed(1)}%</div>
      </div>

      <div className="mt-3 text-sm text-gray-700 p-3 bg-gray-50 rounded border border-gray-100">
        <span className="font-semibold block mb-1">Engine Rationale:</span>
        {rationale}
      </div>
    </div>
  );
}
