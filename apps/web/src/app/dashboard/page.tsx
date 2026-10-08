import type { Metadata } from "next";
import { PortfolioManager } from "@/components/account/PortfolioManager";
import { PortfolioTabs } from "@/components/account/PortfolioTabs";

export const metadata: Metadata = {
  title: "My portfolios",
  description: "Your saved portfolios, valued from the latest stored DSE close. Shown only to the signed-in owner.",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PortfolioTabs />
      <h1 className="text-2xl font-semibold tracking-tight">My portfolios</h1>
      <PortfolioManager />
    </div>
  );
}
