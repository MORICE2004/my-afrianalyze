"use client";

import React from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function YieldCurveChart({ points }: { points: { tenor: string; yield: number }[] }) {
  return (
    <div className="h-64 w-full" data-testid="yield-curve">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis dataKey="tenor" tick={{ fontSize: 12 }} />
          <YAxis tickFormatter={(v: number) => `${v.toFixed(1)}%`} tick={{ fontSize: 12 }} width={48} domain={["auto", "auto"]} />
          <Tooltip formatter={(v) => [`${Number(v).toFixed(2)}%`, "Weighted avg YTM"]} />
          <Line type="monotone" dataKey="yield" stroke="#0b2545" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
