import type { Metadata } from "next";
import React from "react";
import { EmptyState, ErrorState } from "@/components/ui/NotAvailable";
import { apiGet } from "@/lib/api";

export const metadata: Metadata = {
  title: "My portfolios",
  description: "Your saved portfolios. Shown only for a signed-in user.",
};

export default async function DashboardPage() {
  const res = await apiGet<{ portfolios: unknown[] }>("/api/v1/portfolios");
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">My portfolios</h1>
      {res.ok ? (
        <EmptyState title="No saved portfolios">Portfolios you save will appear here.</EmptyState>
      ) : res.status === 401 ? (
        <EmptyState title="Sign in to see your portfolios">
          {res.error} This page only ever shows data saved by the signed-in user.
        </EmptyState>
      ) : (
        <ErrorState message={res.error} />
      )}
    </div>
  );
}
