"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CreditCard, MessageSquare } from "lucide-react";
import type { ActivityItem } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  if (items.length === 0) {
    return (
      <div className="grid h-[220px] place-items-center text-sm text-muted-foreground">
        The live activity feed will stream here.
      </div>
    );
  }

  return (
    <ul className="space-y-1.5">
      <AnimatePresence initial={false}>
        {items.map((it) => {
          const Icon = it.kind === "transaction" ? CreditCard : MessageSquare;
          return (
            <motion.li
              key={it.id}
              layout
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2.5 rounded-lg px-2 py-1.5"
            >
              <span className={cn("size-2 shrink-0 rounded-full",
                it.is_threat ? "bg-danger" : "bg-success")} />
              <Icon className="size-3.5 shrink-0 text-muted-foreground" />
              <span className="min-w-0 flex-1 truncate text-xs text-foreground/85">
                {it.label}
              </span>
              <span className={cn("shrink-0 text-xs font-semibold tabular-nums",
                it.is_threat ? "text-danger" : "text-success")}>
                {Math.round(it.probability * 100)}%
              </span>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}
