import type { Metadata } from "next";
import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { ScamAnalyzer } from "@/components/scam/scam-analyzer";

export const metadata: Metadata = {
  title: "Scam Detector",
  description:
    "AI scam detection for messages — Safe, Suspicious or Scam, with the exact suspicious words highlighted and a plain-English explanation.",
};

export default function ScamPage() {
  return (
    <>
      <Navbar />
      <main className="pt-28 pb-20 mesh">
        <div className="container max-w-3xl">
          <div className="mb-8 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              Model 1 · Scam Detection
            </p>
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Safe, Suspicious, or Scam?
            </h1>
            <p className="mt-3 text-muted-foreground">
              Paste any message. Our TF-IDF + Logistic Regression model returns a
              three-way verdict, the words that triggered it, and why — in plain
              English.
            </p>
          </div>
          <ScamAnalyzer />
          <p className="mt-6 text-center text-xs text-muted-foreground">
            SecureNaija gives guidance, not financial or legal advice. When in
            doubt, contact your bank through its official channels.
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
