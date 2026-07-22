"use client";

import { AnimatePresence, motion } from "framer-motion";
import { MessageSquare } from "lucide-react";
import type { RecentMessage, ScamLabel } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABEL_STYLE: Record<ScamLabel, string> = {
  Scam: "border-danger/30 bg-danger/10 text-danger",
  Suspicious: "border-warning/30 bg-warning/10 text-warning",
  Safe: "border-success/30 bg-success/10 text-success",
};

export function RecentMessages({ messages }: { messages: RecentMessage[] }) {
  if (messages.length === 0) {
    return (
      <div className="grid h-[200px] place-items-center text-sm text-muted-foreground">
        Scanned messages will appear here.
      </div>
    );
  }
  return (
    <ul className="space-y-2">
      <AnimatePresence initial={false}>
        {messages.map((m) => (
          <motion.li
            key={m.id}
            layout
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-3 rounded-xl border border-border/70 p-3"
          >
            <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-lg bg-secondary">
              <MessageSquare className="size-4 text-muted-foreground" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-foreground/90">{m.text}</p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                {m.channel.toUpperCase()} · {m.region} ·{" "}
                {new Date(m.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
            <span className={cn("shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold",
              LABEL_STYLE[m.label])}>
              {m.label} {Math.round(m.probability * 100)}%
            </span>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
