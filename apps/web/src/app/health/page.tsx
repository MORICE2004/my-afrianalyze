import React from 'react';

export default function DataHealthDashboard() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Data Health Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* DSE Connection Status */}
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-2">DSE Connection</h2>
          <div className="flex items-center text-green-600">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            Healthy
          </div>
          <p className="text-sm text-gray-500 mt-2">Last sync: 2 mins ago</p>
        </div>

        {/* Database Status */}
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-2">Database</h2>
          <div className="flex items-center text-green-600">
            <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
            Healthy
          </div>
          <p className="text-sm text-gray-500 mt-2">Latency: 12ms</p>
        </div>

        {/* LLM Status */}
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-2">LLM Service</h2>
          <div className="flex items-center text-yellow-600">
            <span className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></span>
            Degraded
          </div>
          <p className="text-sm text-gray-500 mt-2">Latency: 1200ms</p>
        </div>
      </div>
    </div>
  );
}
