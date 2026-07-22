"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";
import type { Assessment } from "@/lib/types";
import { riskTheme } from "@/lib/risk";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { RiskGauge } from "./risk-gauge";

export function ResultCard({ assessment }: { assessment: Assessment }) {
  const theme = riskTheme(assessment.risk_band);
  const Icon = assessment.is_fraud
    ? assessment.risk_band === "elevated"
      ? ShieldAlert
      : AlertTriangle
    : ShieldCheck;

  const maxWeight =
    Math.max(...assessment.factors.map((f) => Math.abs(f.weight)), 0.0001) || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "overflow-hidden rounded-2xl border bg-card ring-1",
        theme.ring,
      )}
    >
      {/* Header band */}
      <div className={cn("flex items-center gap-3 px-6 py-4", theme.bg)}>
        <Icon className={cn("size-5", theme.text)} />
        <div className="flex-1">
          <p className={cn("text-sm font-bold", theme.text)}>
            {assessment.risk_label}
          </p>
          <p className="text-xs text-muted-foreground">
            {assessment.is_fraud
              ? "This message shows strong signs of fraud."
              : "No strong fraud signals detected."}
          </p>
        </div>
        <Badge variant="outline" className="hidden sm:inline-flex">
          model {assessment.model_version}
        </Badge>
      </div>

      <div className="grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center">
        <div className="mx-auto">
          <RiskGauge
            probability={assessment.fraud_probability}
            band={assessment.risk_band}
          />
        </div>

        <div className="space-y-4">
          <p className="text-sm leading-relaxed text-foreground/90">
            {assessment.verdict}
          </p>

          {assessment.factors.length > 0 && (
            <div className="space-y-2.5">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Why - top signals
              </p>
              {assessment.factors.map((f, i) => {
                const isFraud = f.signal === "fraud";
                return (
                  <motion.div
                    key={f.label + i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.15 + i * 0.06 }}
                    className="space-y-1"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground/90">
                        {f.label}
                      </span>
                      <span
                        className={cn(
                          "font-semibold",
                          isFraud ? "text-danger" : "text-success",
                        )}
                      >
                        {isFraud ? "↑ raises risk" : "↓ lowers risk"}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                      <motion.div
                        className={cn(
                          "h-full rounded-full",
                          isFraud ? "bg-danger" : "bg-success",
                        )}
                        initial={{ width: 0 }}
                        animate={{ width: `${(Math.abs(f.weight) / maxWeight) * 100}%` }}
                        transition={{ delay: 0.2 + i * 0.06, duration: 0.5 }}
                      />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
