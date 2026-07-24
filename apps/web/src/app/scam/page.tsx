import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { ScamAnalyzer } from "@/components/scam/scam-analyzer";
import { HowItWorks } from "@/components/app/how-it-works";

export const metadata: Metadata = {
  title: "Scam Detector",
  description:
    "AI scam detection for messages - Safe, Suspicious or Scam, with the exact suspicious words highlighted and a plain-English explanation.",
};

const STEPS = [
  "Paste any suspicious SMS, WhatsApp message, loan or POS alert.",
  "A TF-IDF + Logistic Regression model returns a three-way verdict - Safe, Suspicious or Scam - with a scam probability and confidence.",
  "Exact linear contributions highlight the words that triggered the verdict, so you can see why it was flagged - not just that it was.",
  "A plain-English explanation tells you what the message is doing and what to do next.",
];

const ADVANTAGES = [
  "Instant (<1s) and runs offline - no LLM API calls, so it is cheap, private and always available.",
  "Explainable: it highlights the exact trigger words instead of returning an opaque yes/no.",
  "Nigeria-tuned: trained on real Nigerian fraud SMS alongside UCI spam, so it knows local scam patterns (fake BVN blocks, palliatives, instant loans).",
  "Three-way verdict: borderline messages are surfaced as Suspicious rather than wrongly cleared.",
  "Free for citizens and a drop-in API for banks - the same model powers both.",
];

export default function ScamPage() {
  return (
    <AppShell>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <PageHeader
          eyebrow="Model 1 · Scam Detection"
          title="Safe, Suspicious, or Scam?"
          description="Paste any message. Our TF-IDF + Logistic Regression model returns a three-way verdict, the words that triggered it, and why - in plain English."
        />
        <ScamAnalyzer />
        <HowItWorks steps={STEPS} advantages={ADVANTAGES} />
        <p className="footnote">
          No Gree AI gives guidance, not financial or legal advice. When in doubt, contact your bank through its official channels.
        </p>
      </div>
    </AppShell>
  );
}
