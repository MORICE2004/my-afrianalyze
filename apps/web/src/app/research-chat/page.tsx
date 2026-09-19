import type { Metadata } from "next";
import React from "react";
import { EmptyState } from "@/components/ui/NotAvailable";

export const metadata: Metadata = {
  title: "Research copilot",
  description: "The research copilot is not available yet.",
};

export default function ResearchCopilotPage() {
  return (
    <EmptyState title="Research copilot is not available">
      The previous version of this page showed a scripted answer with figures that did not come from any source, so it
      has been switched off. The copilot will return once it answers only from stored, cited documents.
    </EmptyState>
  );
}
