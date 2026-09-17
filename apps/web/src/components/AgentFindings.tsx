interface AgentFindingsProps {
  symbol: string;
}

export function AgentFindings({ symbol }: AgentFindingsProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-xl font-bold mb-4 text-gray-900 border-b pb-2">Agent Findings</h3>
      
      <div className="space-y-4">
        <div className="flex gap-4 p-4 bg-red-50 rounded-md border border-red-100">
          <div className="text-red-500 mt-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h4 className="font-semibold text-red-900">Auditor Flags</h4>
            <p className="text-sm text-red-800 mt-1">
              Qualified opinion noted in FY2025 Annual Report regarding valuation of certain unlisted securities.
            </p>
          </div>
        </div>

        <div className="flex gap-4 p-4 bg-yellow-50 rounded-md border border-yellow-100">
          <div className="text-yellow-500 mt-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="font-semibold text-yellow-900">Macro Analysis</h4>
            <p className="text-sm text-yellow-800 mt-1">
              Exposure to FX risk due to significant USD-denominated debt. Recent local currency depreciation may impact margins in H2.
            </p>
          </div>
        </div>

        <div className="flex gap-4 p-4 bg-green-50 rounded-md border border-green-100">
          <div className="text-green-500 mt-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="font-semibold text-green-900">Market Dynamics</h4>
            <p className="text-sm text-green-800 mt-1">
              Strong dominant market share (&gt;65%) provides significant pricing power to offset inflationary pressures.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
