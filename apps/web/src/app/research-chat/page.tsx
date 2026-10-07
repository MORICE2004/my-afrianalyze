import type { Metadata } from "next";
import { CopilotPanel } from "@/components/copilot/CopilotPanel";

export const metadata: Metadata = {
  title: "Research copilot",
  description: "Ask about a company's research. Answers use only AfriEdge's stored, cited figures and say where each comes from.",
};

export default function ResearchCopilotPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-bold tracking-tight">Research copilot</h1>
      <p className="text-sm text-neutral-700">
        Ask about a company&apos;s research. The copilot only sees that company&apos;s research run: the figures from its
        annual reports, AfriEdge&apos;s calculations and what is missing. Every number in an answer is checked against
        those figures before it is shown; an answer that cites anything else is withheld.
      </p>
      <CopilotPanel />
    </div>
  );
}
