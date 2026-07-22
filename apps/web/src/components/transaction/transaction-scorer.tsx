"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, CreditCard, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { TransactionResult, TxnDecision } from "@/lib/types";
import { riskTheme } from "@/lib/risk";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { RiskGauge } from "@/components/detector/risk-gauge";

type Form = {
  TransactionAmt: string;
  ProductCD: string;
  card4: string;
  card6: string;
  P_emaildomain: string;
  C1: string;
  C13: string;
};

const PRESETS: { label: string; values: Partial<Form> }[] = [
  {
    label: "Everyday POS (₦6,500)",
    values: { TransactionAmt: "6500", ProductCD: "W", card4: "verve", card6: "debit", P_emaildomain: "gmail.com", C1: "1", C13: "1" },
  },
  {
    label: "High-risk transfer (₦1.85m)",
    values: { TransactionAmt: "1850000", ProductCD: "C", card4: "mastercard", card6: "credit", P_emaildomain: "outlook.com", C1: "48", C13: "62" },
  },
];

const PRODUCTS = ["W", "C", "R", "H", "S"];
const NETWORKS = ["verve", "visa", "mastercard"];
const CARD_TYPES = ["debit", "credit"];

const DECISION_UI: Record<TxnDecision, { icon: typeof CheckCircle2; text: string; ring: string; bg: string }> = {
  approve: { icon: CheckCircle2, text: "text-success", ring: "ring-success/30", bg: "bg-success/10" },
  review: { icon: AlertTriangle, text: "text-warning", ring: "ring-warning/30", bg: "bg-warning/10" },
  decline: { icon: XCircle, text: "text-danger", ring: "ring-danger/30", bg: "bg-danger/10" },
};

const EMPTY: Form = {
  TransactionAmt: "", ProductCD: "W", card4: "verve", card6: "debit",
  P_emaildomain: "", C1: "", C13: "",
};

export function TransactionScorer() {
  const [form, setForm] = useState<Form>(EMPTY);

  const mutation = useMutation<TransactionResult, Error, void>({
    mutationFn: () => {
      const features: Record<string, number | string | null> = {};
      if (form.TransactionAmt) features.TransactionAmt = Number(form.TransactionAmt);
      if (form.ProductCD) features.ProductCD = form.ProductCD;
      if (form.card4) features.card4 = form.card4;
      if (form.card6) features.card6 = form.card6;
      if (form.P_emaildomain) features.P_emaildomain = form.P_emaildomain;
      if (form.C1) features.C1 = Number(form.C1);
      if (form.C13) features.C13 = Number(form.C13);
      return api.scoreTransaction(features);
    },
  });

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The transaction-fraud model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the SecureNaija API. Is it running?"
        : null;

  const result = mutation.data;
  const decisionUi = result ? DECISION_UI[result.decision] : DECISION_UI.approve;
  const theme = result ? riskTheme(result.risk_band) : riskTheme("minimal");
  const DecisionIcon = decisionUi.icon;
  const maxWeight = result
    ? Math.max(...result.factors.map((f) => Math.abs(f.weight)), 0.0001) || 1
    : 1;

  const selectCls =
    "flex h-11 w-full rounded-xl border border-input bg-background/60 px-4 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <div className="mb-4 flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Presets:</span>
          {PRESETS.map((p) => (
            <button
              key={p.label}
              onClick={() => {
                setForm({ ...EMPTY, ...p.values });
                mutation.reset();
              }}
              className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/70"
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="amt">Amount (₦)</Label>
            <Input id="amt" type="number" inputMode="decimal" placeholder="e.g. 25,000"
              value={form.TransactionAmt} onChange={set("TransactionAmt")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Purchaser email domain</Label>
            <Input id="email" placeholder="e.g. gmail.com"
              value={form.P_emaildomain} onChange={set("P_emaildomain")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="product">Product category</Label>
            <select id="product" className={selectCls} value={form.ProductCD} onChange={set("ProductCD")}>
              {PRODUCTS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="network">Card network</Label>
            <select id="network" className={selectCls} value={form.card4} onChange={set("card4")}>
              {NETWORKS.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ctype">Card type</Label>
            <select id="ctype" className={selectCls} value={form.card6} onChange={set("card6")}>
              {CARD_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="c1">Activity C1</Label>
              <Input id="c1" type="number" placeholder="opt." value={form.C1} onChange={set("C1")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c13">Activity C13</Label>
              <Input id="c13" type="number" placeholder="opt." value={form.C13} onChange={set("C13")} />
            </div>
          </div>
        </div>

        <div className="mt-5 flex items-center justify-between gap-3">
          <p className="text-xs text-muted-foreground">
            Any field left blank is imputed by the model.
          </p>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="min-w-[150px]">
            {mutation.isPending ? (
              <><Loader2 className="animate-spin" /> Scoring…</>
            ) : (
              <><CreditCard /> Score transaction</>
            )}
          </Button>
        </div>

        {errorText && (
          <p className="mt-3 rounded-lg bg-danger/10 px-3 py-2 text-xs font-medium text-danger">
            {errorText}
          </p>
        )}
      </div>

      <AnimatePresence mode="wait">
        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className={cn("overflow-hidden rounded-2xl border bg-card ring-1", decisionUi.ring)}
          >
            <div className={cn("flex items-center gap-3 px-6 py-4", decisionUi.bg)}>
              <DecisionIcon className={cn("size-5", decisionUi.text)} />
              <div className="flex-1">
                <p className={cn("text-sm font-bold capitalize", decisionUi.text)}>
                  {result.decision}
                </p>
                <p className="text-xs text-muted-foreground">
                  <span className="capitalize">{result.risk_band}</span> risk ·{" "}
                  {Math.round(result.fraud_probability * 100)}% probability ·{" "}
                  {Math.round(result.confidence * 100)}% confidence
                </p>
              </div>
              <Badge variant="outline" className="hidden sm:inline-flex">
                {result.algorithm} · {result.model_version}
              </Badge>
            </div>

            <div className="grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center">
              <div className="mx-auto">
                <RiskGauge probability={result.fraud_probability} band={result.risk_band} />
              </div>

              <div className="space-y-4">
                <p className="text-sm leading-relaxed text-foreground/90">{result.verdict}</p>

                <div className="rounded-xl border border-border bg-muted/30 p-3">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    What this means
                  </p>
                  <p className="mt-1 text-sm text-foreground/90">{result.risk_explanation}</p>
                </div>

                {result.factors.length > 0 && (
                  <div className="space-y-2.5">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Why - top reasons (SHAP)
                    </p>
                    {result.factors.map((f, i) => {
                      const isFraud = f.signal === "fraud";
                      return (
                        <div key={f.feature + i} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-medium text-foreground/90">{f.label}</span>
                            <span className={cn("font-semibold", isFraud ? "text-danger" : "text-success")}>
                              {isFraud ? "↑ raises risk" : "↓ lowers risk"}
                            </span>
                          </div>
                          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                            <motion.div
                              className={cn("h-full rounded-full", isFraud ? "bg-danger" : "bg-success")}
                              initial={{ width: 0 }}
                              animate={{ width: `${(Math.abs(f.weight) / maxWeight) * 100}%` }}
                              transition={{ delay: 0.2 + i * 0.06, duration: 0.5 }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
