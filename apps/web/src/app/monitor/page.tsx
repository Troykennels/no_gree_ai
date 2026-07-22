import type { Metadata } from "next";
import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { FraudDashboard } from "@/components/monitor/fraud-dashboard";

export const metadata: Metadata = {
  title: "Fraud Intelligence Dashboard",
  description:
    "A real-time fraud command center - security score, risk score, threat timeline, heatmap, analytics, recent messages and transactions, and live alerts, all updating automatically.",
};

export default function MonitorPage() {
  return (
    <>
      <Navbar />
      <main className="pt-24 pb-20">
        <div className="container">
          <FraudDashboard />
        </div>
      </main>
      <Footer />
    </>
  );
}
