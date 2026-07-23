import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { TransactionScorer } from "@/components/transaction/transaction-scorer";

export const metadata: Metadata = {
  title: "Transaction Fraud Scoring",
  description:
    "Score a card transaction for fraud with an XGBoost model trained on the IEEE-CIS dataset - decision, probability and SHAP explanation.",
};

export default function TransactionPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Model 2 · Transaction Fraud"
          title="Score a card transaction"
          description="A gradient-boosted model trained and evaluated out-of-time on the IEEE-CIS fraud dataset. Enter what you know - the rest is imputed - and get an approve / review / decline decision with a SHAP explanation."
        />
        <TransactionScorer />
        <p className="mt-6 text-center text-xs text-muted-foreground">
          Model selected by PR-AUC (right metric for a ~3.5% fraud base rate).
          Scores are decision support, not a final authorization.
        </p>
      </div>
    </AppShell>
  );
}
