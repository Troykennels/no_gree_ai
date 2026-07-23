import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { ScamAnalyzer } from "@/components/scam/scam-analyzer";

export const metadata: Metadata = {
  title: "Scam Detector",
  description:
    "AI scam detection for messages - Safe, Suspicious or Scam, with the exact suspicious words highlighted and a plain-English explanation.",
};

export default function ScamPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Model 1 · Scam Detection"
          title="Safe, Suspicious, or Scam?"
          description="Paste any message. Our TF-IDF + Logistic Regression model returns a three-way verdict, the words that triggered it, and why - in plain English."
        />
        <ScamAnalyzer />
        <p className="mt-6 text-center text-xs text-muted-foreground">
          No_Gree AI gives guidance, not financial or legal advice. When in doubt,
          contact your bank through its official channels.
        </p>
      </div>
    </AppShell>
  );
}
