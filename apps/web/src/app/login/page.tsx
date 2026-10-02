import type { Metadata } from "next";
import { SignInForm } from "@/components/account/SignInForm";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AfriEdge to keep your own portfolios.",
};

export default function LoginPage() {
  return (
    <div className="max-w-md mx-auto space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Sign in to AfriEdge</h1>
      <p className="text-sm text-neutral-600">
        Research pages are open to everyone. An account only keeps your own portfolios, which no one else can see.
      </p>
      <SignInForm />
    </div>
  );
}
