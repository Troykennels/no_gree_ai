import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { IntelligenceConsole } from "@/components/intelligence/intelligence-console";

export const metadata: Metadata = {
  title: "Fraud Intelligence",
  description:
    "Combine scam detection and transaction fraud into one 0-100 risk score, a category, and instant AI recommendations you can act on.",
};

export default function IntelligencePage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Fraud Intelligence Engine"
          title="One score. One clear plan."
          description="We fuse the scam and transaction-fraud models into a single 0-100 risk score, a category from Safe to Critical, and instant AI recommendations - exactly what to do next."
        />
        <IntelligenceConsole />
        <p className="mt-6 text-center text-xs text-muted-foreground">
          No_Gree AI gives guidance, not financial or legal advice. When in doubt,
          contact your bank through its official channels.
        </p>
      </div>
    </AppShell>
  );
}
