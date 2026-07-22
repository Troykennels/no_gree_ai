"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, ShieldCheck, ShieldAlert, AlertTriangle, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { RiskBand, ScamLabel, ScamResult } from "@/lib/types";
import { riskTheme } from "@/lib/risk";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { RiskGauge } from "@/components/detector/risk-gauge";

const SAMPLES: { label: string; text: string }[] = [
  {
    label: "Fake bank alert",
    text: "Dear Customer, your GTBank account will be BLOCKED today. Update your BVN now via http://gtb-verify.top/login to avoid deactivation.",
  },
  {
    label: "Loan scam",
    text: "CONGRATULATIONS! You are pre-approved for an instant loan of N150,000, NO collateral. Pay a small processing fee to unlock. Apply: bit.ly/loan-ng",
  },
  {
    label: "Real credit alert",
    text: "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Desc:Transfer from Chidi. Bal:NGN61,300.",
  },
];

const LABEL_BAND: Record<ScamLabel, RiskBand> = {
  Scam: "high",
  Suspicious: "elevated",
  Safe: "minimal",
};

const LABEL_ICON = {
  Scam: AlertTriangle,
  Suspicious: ShieldAlert,
  Safe: ShieldCheck,
};

export function ScamAnalyzer() {
  const [message, setMessage] = useState("");

  const mutation = useMutation<ScamResult, Error, void>({
    mutationFn: () => api.detectScam(message.trim()),
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The scam-detection model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the SecureNaija API. Is it running?"
        : null;

  const result = mutation.data;
  const band = result ? LABEL_BAND[result.label] : "minimal";
  const theme = riskTheme(band);
  const Icon = result ? LABEL_ICON[result.label] : ShieldCheck;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <Textarea
          aria-label="Message to check for a scam"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste the suspicious SMS, WhatsApp message or email here…"
          maxLength={5000}
          className="min-h-[140px]"
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Try:</span>
            {SAMPLES.map((s) => (
              <button
                key={s.label}
                onClick={() => {
                  setMessage(s.text);
                  mutation.reset();
                }}
                className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-secondary/70"
              >
                {s.label}
              </button>
            ))}
          </div>

          <Button
            onClick={() => mutation.mutate()}
            disabled={!message.trim() || mutation.isPending}
            className="min-w-[150px]"
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="animate-spin" /> Analyzing…
              </>
            ) : (
              <>
                <Sparkles /> Check for scam
              </>
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
        {result ? (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className={cn("overflow-hidden rounded-2xl border bg-card ring-1", theme.ring)}
          >
            <div className={cn("flex items-center gap-3 px-6 py-4", theme.bg)}>
              <Icon className={cn("size-5", theme.text)} />
              <div className="flex-1">
                <p className={cn("text-sm font-bold", theme.text)}>{result.label}</p>
                <p className="text-xs text-muted-foreground">
                  Confidence {Math.round(result.confidence * 100)}%
                </p>
              </div>
              <Badge variant="outline" className="hidden sm:inline-flex">
                model {result.model_version}
              </Badge>
            </div>

            <div className="grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center">
              <div className="mx-auto">
                <RiskGauge probability={result.scam_probability} band={band} />
              </div>

              <div className="space-y-4">
                <p className="text-sm leading-relaxed text-foreground/90">
                  {result.explanation}
                </p>

                {result.highlighted_words.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Suspicious words
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.highlighted_words.map((w, i) => (
                        <motion.span
                          key={w.word + i}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.1 + i * 0.05 }}
                          className="rounded-full border border-danger/30 bg-danger/10 px-2.5 py-1 text-xs font-medium text-danger"
                        >
                          {w.word}
                        </motion.span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
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
            Your Safe / Suspicious / Scam verdict will appear here.
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
