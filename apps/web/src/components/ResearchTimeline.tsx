"use client";

import React from "react";
import { captureEvent } from "../lib/telemetry";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description: string;
  status: "pending" | "in-progress" | "completed" | "failed";
}

interface ResearchTimelineProps {
  events: TimelineEvent[];
  symbol: string;
}

export function ResearchTimeline({ events, symbol }: ResearchTimelineProps) {
  // Track that the timeline was viewed
  React.useEffect(() => {
    captureEvent("research_timeline_viewed", { symbol });
  }, [symbol]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Research Timeline</h3>
      <div className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="relative flex gap-4">
            {/* Timeline line */}
            {index !== events.length - 1 && (
              <div className="absolute left-2.5 top-6 bottom-[-1rem] w-0.5 bg-gray-200"></div>
            )}
            
            {/* Status dot */}
            <div className={`relative z-10 w-5 h-5 rounded-full border-2 bg-white mt-1 shrink-0 ${
              event.status === "completed" ? "border-green-500 bg-green-500" :
              event.status === "failed" ? "border-red-500 bg-red-500" :
              event.status === "in-progress" ? "border-blue-500 bg-blue-100" :
              "border-gray-300"
            }`} />
            
            {/* Content */}
            <div className="flex-1 pb-4">
              <div className="flex justify-between items-start">
                <h4 className="text-sm font-medium text-gray-900">{event.title}</h4>
                <time className="text-xs text-gray-500">{new Date(event.timestamp).toLocaleTimeString()}</time>
              </div>
              <p className="text-sm text-gray-600 mt-1">{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
