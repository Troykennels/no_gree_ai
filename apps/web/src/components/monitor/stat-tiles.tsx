"use client";

import { motion } from "framer-motion";
import { MessageSquareWarning, CreditCard, ShieldAlert, BadgeCheck, Banknote, Brain } from "lucide-react";
import type { AutomationStats } from "@/lib/types";
import { Card } from "@/components/ui/card";

function naira(n: number): string {
  if (n >= 1_000_000) return `₦${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `₦${(n / 1_000).toFixed(1)}k`;
  return `₦${Math.round(n)}`;
}

export function StatTiles({ stats }: { stats: AutomationStats }) {
  const tiles = [
    { label: "Messages scanned", value: stats.messages_scanned, icon: MessageSquareWarning, accent: "text-primary" },
    { label: "Transactions analyzed", value: stats.transactions_analyzed, icon: CreditCard, accent: "text-primary" },
    { label: "Scams detected", value: stats.scams_detected, icon: ShieldAlert, accent: "text-danger" },
    { label: "Frauds blocked", value: stats.frauds_blocked, icon: BadgeCheck, accent: "text-danger" },
    { label: "Value protected", value: naira(stats.value_protected), icon: Banknote, accent: "text-success" },
    { label: "Feedback learned", value: stats.feedback_count, icon: Brain, accent: "text-success" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {tiles.map((t) => {
        const Icon = t.icon;
        return (
          <Card key={t.label} className="p-4">
            <div className="flex items-center justify-between">
              <span className="grid size-9 place-items-center rounded-lg bg-secondary">
                <Icon className={`size-4 ${t.accent}`} />
              </span>
            </div>
            <motion.p
              key={String(t.value)}
              initial={{ opacity: 0.4, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-3 text-2xl font-bold tabular-nums"
            >
              {t.value}
            </motion.p>
            <p className="mt-0.5 text-xs text-muted-foreground">{t.label}</p>
          </Card>
        );
      })}
    </div>
  );
}
