import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { TransactionScorer } from "@/components/transaction/transaction-scorer";
import { HowItWorks } from "@/components/app/how-it-works";

export const metadata: Metadata = {
  title: "Transaction Fraud Scoring",
  description:
    "Score a card transaction for fraud with an XGBoost model trained on the IEEE-CIS dataset - decision, probability and SHAP explanation.",
};

const STEPS = [
  "Enter what you know about the transaction — amount, card network, product, purchaser email — or pick a preset. Any field you leave blank is imputed exactly as it was in training.",
  "An XGBoost model (trained and tested out-of-time on the IEEE-CIS dataset) returns a calibrated fraud probability and an approve / review / decline decision.",
  "TreeSHAP explains the decision per-transaction — which signals raised risk and which lowered it — so there is no black box.",
  "Push it to the live engine and the transaction is scored, alerted, and folded into the security score, heatmap and alerts automatically — in real time, no refresh.",
];

const ADVANTAGES = [
  "Effective: the model is chosen by PR-AUC — the right metric at a ~3.5% fraud base rate — and validated out-of-time, so it never learns from the future.",
  "Explainable: every decision ships with signed SHAP reasons, which regulators and risk teams can audit.",
  "Automated: auto-scores as you type and streams straight into always-on monitoring — one scored transaction updates the whole command center.",
  "Flexible: send only the fields you have; the rest are imputed, so partial data still returns a calibrated score.",
  "Actionable: approve / review / decline maps directly onto a bank or fintech's decisioning workflow.",
];

export default function TransactionPage() {
  return (
    <AppShell>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <PageHeader
          eyebrow="Model 2 · Transaction Fraud"
          title="Score a card transaction"
          description="A gradient-boosted model trained and evaluated out-of-time on the IEEE-CIS fraud dataset. Enter what you know — the rest is imputed — and get an approve / review / decline decision with a SHAP explanation. Turn on Auto-score for live scoring, then push it into the automation engine."
        />
        <TransactionScorer />
        <HowItWorks steps={STEPS} advantages={ADVANTAGES} />
        <p className="footnote">
          Model selected by PR-AUC (right metric for a ~3.5% fraud base rate). Scores are decision support, not a final authorization.
        </p>
      </div>
    </AppShell>
  );
}
