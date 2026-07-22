import type { Metadata } from "next";
import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { IntelligenceConsole } from "@/components/intelligence/intelligence-console";

export const metadata: Metadata = {
  title: "Fraud Intelligence",
  description:
    "Combine scam detection and transaction fraud into one 0–100 risk score, a category, and instant AI recommendations you can act on.",
};

export default function IntelligencePage() {
  return (
    <>
      <Navbar />
      <main className="pt-28 pb-20 mesh">
        <div className="container max-w-3xl">
          <div className="mb-8 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              Fraud Intelligence Engine
            </p>
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              One score. One clear plan.
            </h1>
            <p className="mt-3 text-muted-foreground">
              We fuse the scam and transaction-fraud models into a single 0–100 risk
              score, a category from Safe to Critical, and instant AI recommendations —
              exactly what to do next.
            </p>
          </div>
          <IntelligenceConsole />
          <p className="mt-6 text-center text-xs text-muted-foreground">
            SecureNaija gives guidance, not financial or legal advice. When in doubt,
            contact your bank through its official channels.
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
