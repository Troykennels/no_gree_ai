import type { Metadata } from "next";
import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { TransactionScorer } from "@/components/transaction/transaction-scorer";

export const metadata: Metadata = {
  title: "Transaction Fraud Scoring",
  description:
    "Score a card transaction for fraud with an XGBoost model trained on the IEEE-CIS dataset — decision, probability and SHAP explanation.",
};

export default function TransactionPage() {
  return (
    <>
      <Navbar />
      <main className="pt-28 pb-20 mesh">
        <div className="container max-w-3xl">
          <div className="mb-8 text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-primary">
              Model 2 · Transaction Fraud
            </p>
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Score a card transaction
            </h1>
            <p className="mt-3 text-muted-foreground">
              A gradient-boosted model trained and evaluated out-of-time on the
              IEEE-CIS fraud dataset. Enter what you know — the rest is imputed —
              and get an approve / review / decline decision with a SHAP
              explanation.
            </p>
          </div>
          <TransactionScorer />
          <p className="mt-6 text-center text-xs text-muted-foreground">
            Model selected by PR-AUC (right metric for a ~3.5% fraud base rate).
            Scores are decision support, not a final authorization.
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
