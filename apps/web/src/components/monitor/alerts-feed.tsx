"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, ShieldAlert, Check } from "lucide-react";
import type { EngineAlert } from "@/lib/types";
import { cn } from "@/lib/utils";

export function AlertsFeed({
  alerts,
  onFeedback,
}: {
  alerts: EngineAlert[];
  onFeedback: (alert: EngineAlert, label: "Safe" | "Scam") => void;
}) {
  if (alerts.length === 0) {
    return (
      <div className="grid h-[220px] place-items-center text-center text-sm text-muted-foreground">
        No alerts yet. The engine raises one the instant a threat is scored.
      </div>
    );
  }

  return (
    <ul className="space-y-2.5">
      <AnimatePresence initial={false}>
        {alerts.map((a) => {
          const crit = a.severity === "critical";
          const Icon = crit ? AlertTriangle : ShieldAlert;
          return (
            <motion.li
              key={a.id}
              layout
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={cn(
                "rounded-xl border p-3",
                crit ? "border-danger/25 bg-danger/5" : "border-warning/25 bg-warning/5",
              )}
            >
              <div className="flex items-start gap-2.5">
                <Icon className={cn("mt-0.5 size-4 shrink-0", crit ? "text-danger" : "text-warning")} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-foreground/90">{a.title}</p>
                    <span className={cn("shrink-0 text-xs font-bold tabular-nums",
                      crit ? "text-danger" : "text-warning")}>
                      {Math.round(a.probability * 100)}%
                    </span>
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{a.detail}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {a.region}
                    {a.amount ? ` · ₦${Math.round(a.amount).toLocaleString()}` : ""}
                    {" · "}
                    {new Date(a.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>

                  {a.kind === "message" && (
                    <div className="mt-2 flex items-center gap-2">
                      {a.feedback ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-success">
                          <Check className="size-3.5" /> Marked {a.feedback} · model will learn
                        </span>
                      ) : (
                        <>
                          <span className="text-[11px] text-muted-foreground">Was this right?</span>
                          <button
                            onClick={() => onFeedback(a, "Scam")}
                            className="rounded-full border border-danger/30 bg-danger/10 px-2.5 py-0.5 text-xs font-medium text-danger hover:bg-danger/20"
                          >
                            Scam
                          </button>
                          <button
                            onClick={() => onFeedback(a, "Safe")}
                            className="rounded-full border border-success/30 bg-success/10 px-2.5 py-0.5 text-xs font-medium text-success hover:bg-success/20"
                          >
                            Safe
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}
