import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { FraudDashboard } from "@/components/monitor/fraud-dashboard";

export const metadata: Metadata = {
  title: "Fraud Intelligence Dashboard",
  description:
    "A real-time fraud command center - security score, risk score, threat timeline, heatmap, analytics, recent messages and transactions, and live alerts, all updating automatically.",
};

export default function MonitorPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Live"
        title="Fraud Command Center"
        description="Real-time security score, threat timeline, heatmap, analytics and live alerts - all updating automatically."
      />
      <FraudDashboard />
    </AppShell>
  );
}
