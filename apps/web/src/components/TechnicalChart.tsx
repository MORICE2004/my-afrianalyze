"use client";

import React from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

interface ChartData {
  date: string;
  price: number;
  sma: number;
  ema: number;
  volume: number;
}

interface TechnicalChartProps {
  data: ChartData[];
}

export function TechnicalChart({ data }: TechnicalChartProps) {
  return (
    <div className="w-full h-96 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Technical Analysis Chart</h3>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis yAxisId="left" domain={["auto", "auto"]} />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Bar yAxisId="right" dataKey="volume" fill="#82ca9d" name="Volume" opacity={0.3} />
          <Line yAxisId="left" type="monotone" dataKey="price" stroke="#8884d8" name="Price" strokeWidth={2} dot={false} />
          <Line yAxisId="left" type="monotone" dataKey="sma" stroke="#ff7300" name="SMA" dot={false} />
          <Line yAxisId="left" type="monotone" dataKey="ema" stroke="#413ea0" name="EMA" dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
