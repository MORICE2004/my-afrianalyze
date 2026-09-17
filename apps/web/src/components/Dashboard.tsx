import React, { useEffect } from 'react';
import { posthog } from '../lib/posthog';
import { MultiMarketChart } from './MultiMarketChart';

export const Dashboard: React.FC = () => {
  useEffect(() => {
    // Track when dashboard is viewed
    posthog.capture('dashboard_viewed', {
      timestamp: new Date().toISOString()
    });
  }, []);

  const handleRunResearch = () => {
    posthog.capture('research_run_initiated', {
      markets: ['DSE', 'NSE'],
      module: 'equity_research'
    });
    console.log("Research run initiated.");
    // Actual research run logic would go here
  };

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h1>My AfriAnalyze Dashboard</h1>
      <p>Welcome to the multi-market equity research platform.</p>
      
      <MultiMarketChart />
      
      <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h3>Research Actions</h3>
        <button 
          onClick={handleRunResearch}
          style={{
            padding: '10px 20px',
            backgroundColor: '#000',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Run Multi-Market Analysis
        </button>
      </div>
    </div>
  );
};
