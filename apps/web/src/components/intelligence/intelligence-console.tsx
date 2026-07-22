"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  Loader2, Brain, Sparkles, AlertTriangle, ShieldAlert, AlertCircle,
  Info, ShieldCheck, CreditCard, MessageSquare, ChevronDown,
} from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { IntelligenceResult, Priority, RiskBand, RiskCategory } from "@/lib/types";
import { riskTheme } from "@/lib/risk";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { RiskGauge } from "@/components/detector/risk-gauge";

const CATEGORY_BAND: Record<RiskCategory, RiskBand> = {
  Safe: "minimal", Low: "low", Medium: "elevated", High: "high", Critical: "critical",
};

const PRIORITY_UI: Record<Priority, { icon: typeof AlertTriangle; text: string; card: string }> = {
  critical: { icon: AlertTriangle, text: "text-danger", card: "border-danger/30 bg-danger/5" },
  high: { icon: ShieldAlert, text: "text-danger", card: "border-danger/20 bg-danger/5" },
  medium: { icon: AlertCircle, text: "text-warning", card: "border-warning/25 bg-warning/5" },
  low: { icon: Info, text: "text-muted-foreground", card: "border-border" },
  info: { icon: ShieldCheck, text: "text-success", card: "border-success/25 bg-success/5" },
};

const SAMPLE =
  "Your card **2290 was used for NGN180,000 abroad. If this wasn't you, call 08012345678 and confirm your OTP now to reverse it.";

export function IntelligenceConsole() {
  const [message, setMessage] = useState("");
  const [showTxn, setShowTxn] = useState(false);
  const [amount, setAmount] = useState("");
  const [product, setProduct] = useState("C");
  const [cardType, setCardType] = useState("credit");
  const [email, setEmail] = useState("");

  const mutation = useMutation<IntelligenceResult, Error, void>({
    mutationFn: () => {
      const txn =
        showTxn && (amount || email)
          ? {
              TransactionAmt: amount ? Number(amount) : null,
              ProductCD: product,
              card6: cardType,
              P_emaildomain: email || null,
            }
          : null;
      return api.assessIntelligence(message.trim() || null, txn);
    },
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 400
        ? "Enter a message or add a transaction to assess."
        : mutation.error.status === 503
          ? "The models are still starting up. Try again in a moment."
          : mutation.error.message
      : mutation.error
        ? "Could not reach the SecureNaija API. Is it running?"
        : null;

  const canSubmit = message.trim().length > 0 || (showTxn && (amount || email));
  const result = mutation.data;
  const band = result ? CATEGORY_BAND[result.category] : "minimal";
  const theme = riskTheme(band);
  const selectCls =
    "flex h-11 w-full rounded-xl border border-input bg-background/60 px-4 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

  return (
    <div className="space-y-5">
      {/* Input */}
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <Textarea
          aria-label="Message to assess for fraud"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste a suspicious message (optional if you add a transaction)…"
          maxLength={5000}
          className="min-h-[120px]"
        />

        <button
          onClick={() => setShowTxn((v) => !v)}
          className="mt-3 flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
        >
          <CreditCard className="size-4" />
          {showTxn ? "Remove transaction" : "Add a transaction to combine"}
          <ChevronDown className={cn("size-4 transition-transform", showTxn && "rotate-180")} />
        </button>

        <AnimatePresence>
          {showTxn && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="amt">Amount (₦)</Label>
                  <Input id="amt" type="number" placeholder="e.g. 180,000" value={amount}
                    onChange={(e) => setAmount(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Purchaser email domain</Label>
                  <Input id="email" placeholder="e.g. gmail.com" value={email}
                    onChange={(e) => setEmail(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="prod">Product category</Label>
                  <select id="prod" className={selectCls} value={product}
                    onChange={(e) => setProduct(e.target.value)}>
                    {["W", "C", "R", "H", "S"].map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ctype">Card type</Label>
                  <select id="ctype" className={selectCls} value={cardType}
                    onChange={(e) => setCardType(e.target.value)}>
                    {["debit", "credit"].map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => { setMessage(SAMPLE); mutation.reset(); }}
            className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground hover:bg-secondary/70"
          >
            Try an example
          </button>
          <Button onClick={() => mutation.mutate()} disabled={!canSubmit || mutation.isPending}
            className="min-w-[170px]">
            {mutation.isPending ? (
              <><Loader2 className="animate-spin" /> Assessing…</>
            ) : (
              <><Brain /> Assess fraud risk</>
            )}
          </Button>
        </div>

        {errorText && (
          <p className="mt-3 rounded-lg bg-danger/10 px-3 py-2 text-xs font-medium text-danger">
            {errorText}
          </p>
        )}
      </div>

      {/* Result */}
      <AnimatePresence mode="wait">
        {result ? (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-4"
          >
            {/* Overall score */}
            <div className={cn("overflow-hidden rounded-2xl border bg-card ring-1", theme.ring)}>
              <div className={cn("flex items-center gap-3 px-6 py-4", theme.bg)}>
                <Sparkles className={cn("size-5", theme.text)} />
                <div className="flex-1">
                  <p className={cn("text-sm font-bold", theme.text)}>
                    {result.category} risk
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Risk score {result.overall_risk_score}/100 · Confidence{" "}
                    {Math.round(result.confidence * 100)}%
                  </p>
                </div>
                <div className="hidden gap-1.5 sm:flex">
                  {result.scam && (
                    <Badge variant="outline"><MessageSquare className="size-3" /> {result.scam.label}</Badge>
                  )}
                  {result.transaction && (
                    <Badge variant="outline"><CreditCard className="size-3" /> {result.transaction.decision}</Badge>
                  )}
                </div>
              </div>

              <div className="grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center">
                <div className="mx-auto">
                  <RiskGauge probability={result.overall_risk_score / 100} band={band} />
                </div>
                <div className="space-y-3">
                  <p className="text-sm leading-relaxed text-foreground/90">
                    {result.human_explanation}
                  </p>
                  {result.signals.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {result.signals.map((s, i) => (
                        <span key={`${s.type}-${i}`}
                          className={cn("rounded-full border px-2.5 py-1 text-xs font-medium",
                            PRIORITY_UI[s.severity].card, PRIORITY_UI[s.severity].text)}>
                          {s.label}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Reasons + what this means */}
            <div className="grid gap-4 sm:grid-cols-[1.3fr_1fr]">
              <div className="rounded-2xl border border-border bg-card p-5">
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle className="size-4 text-primary" />
                  <h2 className="font-semibold">Why - reasons</h2>
                </div>
                {result.reasons.length > 0 ? (
                  <ul className="space-y-2">
                    {result.reasons.map((r, i) => (
                      <motion.li key={r + i}
                        initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.04 * i }}
                        className="flex items-center gap-2.5 text-sm text-foreground/90">
                        <span className={cn("size-1.5 shrink-0 rounded-full", theme.text.replace("text-", "bg-"))} />
                        {r}
                      </motion.li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No specific red flags - nothing stood out as fraudulent.
                  </p>
                )}
              </div>
              <div className={cn("rounded-2xl border bg-card p-5 ring-1", theme.ring)}>
                <div className="mb-2 flex items-center gap-2">
                  <ShieldAlert className={cn("size-4", theme.text)} />
                  <h2 className="font-semibold">What this means</h2>
                </div>
                <p className="text-sm leading-relaxed text-foreground/90">
                  {result.risk_explanation}
                </p>
              </div>
            </div>

            {/* AI Recommendations */}
            <div className="rounded-2xl border border-border bg-card p-5 sm:p-6">
              <div className="mb-4 flex items-center gap-2">
                <Brain className="size-4 text-primary" />
                <h2 className="font-semibold">AI recommendations</h2>
                <Badge variant="outline" className="ml-auto">{result.recommendations.length} actions</Badge>
              </div>
              <ul className="space-y-2.5">
                {result.recommendations.map((r, i) => {
                  const ui = PRIORITY_UI[r.priority];
                  const Icon = ui.icon;
                  return (
                    <motion.li
                      key={r.id}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.05 * i }}
                      className={cn("flex items-start gap-3 rounded-xl border p-3", ui.card)}
                    >
                      <Icon className={cn("mt-0.5 size-4 shrink-0", ui.text)} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-foreground/90">{r.action}</p>
                          <span className={cn("text-[10px] font-bold uppercase tracking-wider", ui.text)}>
                            {r.priority}
                          </span>
                        </div>
                        <p className="mt-0.5 text-xs text-muted-foreground">{r.detail}</p>
                      </div>
                    </motion.li>
                  );
                })}
              </ul>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="hint"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center gap-2 rounded-2xl border border-dashed border-border/70 py-10 text-sm text-muted-foreground"
          >
            <Sparkles className="size-4 text-primary" />
            One fused 0-100 score, a risk category, and instant actions will appear here.
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
