import type { Metadata } from "next";
import { PortfolioTabs } from "@/components/account/PortfolioTabs";

export const metadata: Metadata = {
  title: "Portfolio builder",
  description: "Choose a market, capital in that market's currency and a risk profile to request a sourced proposal.",
};

export default function PortfolioLayout({ children }: LayoutProps<"/portfolio">) {
  return (
    <>
      <PortfolioTabs />
      {children}
    </>
  );
}
