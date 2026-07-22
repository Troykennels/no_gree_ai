"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import type { RecentTransaction, TxnDecision } from "@/lib/types";
import { cn } from "@/lib/utils";

const DECISION: Record<TxnDecision, { icon: typeof CheckCircle2; style: string; text: string }> = {
  approve: { icon: CheckCircle2, style: "border-success/30 bg-success/10 text-success", text: "text-success" },
  review: { icon: AlertTriangle, style: "border-warning/30 bg-warning/10 text-warning", text: "text-warning" },
  decline: { icon: XCircle, style: "border-danger/30 bg-danger/10 text-danger", text: "text-danger" },
};

export function RecentTransactions({ transactions }: { transactions: RecentTransaction[] }) {
  if (transactions.length === 0) {
    return (
      <div className="grid h-[200px] place-items-center text-sm text-muted-foreground">
        Analyzed transactions will appear here.
      </div>
    );
  }
  return (
    <ul className="space-y-2">
      <AnimatePresence initial={false}>
        {transactions.map((t) => {
          const d = DECISION[t.decision];
          const Icon = d.icon;
          return (
            <motion.li
              key={t.id}
              layout
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 rounded-xl border border-border/70 p-3"
            >
              <span className={cn("grid size-8 shrink-0 place-items-center rounded-lg border", d.style)}>
                <Icon className="size-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1 text-sm font-semibold text-foreground/90">
                  <ArrowUpRight className="size-3.5 text-muted-foreground" />
                  ₦{Math.round(t.amount).toLocaleString("en-NG")}
                </p>
                <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                  {t.bank ? `${t.bank} · ` : ""}{t.payer ? `${t.payer} · ` : ""}{t.region} ·{" "}
                  {new Date(t.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>
              <span className={cn("shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold capitalize", d.style)}>
                {t.decision} {Math.round(t.probability * 100)}%
              </span>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}
