import React from 'react';

const mockData = [
  { month: 'Jan', dse: 120, nse: 150 },
  { month: 'Feb', dse: 125, nse: 148 },
  { month: 'Mar', dse: 130, nse: 155 },
  { month: 'Apr', dse: 128, nse: 160 },
  { month: 'May', dse: 135, nse: 165 },
  { month: 'Jun', dse: 140, nse: 170 },
];

export const MultiMarketChart: React.FC = () => {
  return (
    <div style={{ padding: '16px', border: '1px solid #ccc', borderRadius: '8px', marginBottom: '16px' }}>
      <h3>Multi-Market Performance: DSE vs NSE</h3>
      <div style={{ display: 'flex', height: '200px', alignItems: 'flex-end', gap: '10px', marginTop: '16px' }}>
        {mockData.map((data, index) => (
          <div key={index} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
            <div style={{ display: 'flex', width: '100%', justifyContent: 'center', gap: '4px', height: '150px', alignItems: 'flex-end' }}>
              <div 
                style={{ 
                  width: '40%', 
                  backgroundColor: '#4A90E2', 
                  height: `${(data.dse / 200) * 100}%`,
                  borderRadius: '4px 4px 0 0'
                }} 
                title={`DSE: ${data.dse}`}
              ></div>
              <div 
                style={{ 
                  width: '40%', 
                  backgroundColor: '#E24A4A', 
                  height: `${(data.nse / 200) * 100}%`,
                  borderRadius: '4px 4px 0 0'
                }}
                title={`NSE: ${data.nse}`}
              ></div>
            </div>
            <span style={{ fontSize: '12px', marginTop: '8px' }}>{data.month}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#4A90E2' }}></div>
          <span style={{ fontSize: '12px' }}>DSE (Tanzania)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '12px', height: '12px', backgroundColor: '#E24A4A' }}></div>
          <span style={{ fontSize: '12px' }}>NSE (Kenya)</span>
        </div>
      </div>
    </div>
  );
};
