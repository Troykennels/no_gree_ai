"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Info, ShieldAlert, AlertTriangle, ShieldX, X } from "lucide-react";
import type { NotificationPriority } from "@/lib/types";
import { cn } from "@/lib/utils";

export interface Toast {
  id: string;
  priority: NotificationPriority;
  title: string;
  body: string;
}

export const PRIORITY_STYLE: Record<NotificationPriority, { ring: string; text: string; Icon: typeof Info }> = {
  info: { ring: "ring-success/30", text: "text-success", Icon: Info },
  warning: { ring: "ring-warning/30", text: "text-warning", Icon: AlertTriangle },
  danger: { ring: "ring-danger/30", text: "text-danger", Icon: ShieldAlert },
  critical: { ring: "ring-danger/50", text: "text-danger", Icon: ShieldX },
};

export function Toaster({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[min(92vw,360px)] flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => {
          const s = PRIORITY_STYLE[t.priority];
          const Icon = s.Icon;
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, x: 40, scale: 0.96 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ duration: 0.25 }}
              className={cn(
                "pointer-events-auto flex items-start gap-2.5 rounded-xl border border-border bg-card/95 p-3 shadow-lg ring-1 backdrop-blur",
                s.ring,
                t.priority === "critical" && "animate-pulse",
              )}
              role="alert"
            >
              <Icon className={cn("mt-0.5 size-4 shrink-0", s.text)} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-foreground/90">{t.title}</p>
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{t.body}</p>
              </div>
              <button
                onClick={() => onDismiss(t.id)}
                className="shrink-0 rounded p-0.5 text-muted-foreground hover:text-foreground"
                aria-label="Dismiss notification"
              >
                <X className="size-3.5" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
