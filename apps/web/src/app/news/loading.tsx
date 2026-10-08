import React from "react";
import { Skeleton } from "@/components/ui/kit";

export default function Loading() {
  return (
    <div className="max-w-3xl space-y-6" aria-label="Loading news">
      <Skeleton className="h-7 w-72" /><Skeleton className="h-4 w-full max-w-xl" />
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="space-y-2 border-t border-line pt-4"><Skeleton className="h-3 w-48" /><Skeleton className="h-5 w-full" /><Skeleton className="h-3 w-32" /></div>
      ))}
    </div>
  );
}
