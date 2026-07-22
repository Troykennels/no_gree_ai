"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const CATEGORIES = ["Safe", "Low", "Medium", "High", "Critical"] as const;

function categoryOf(score: number): number {
  if (score >= 85) return 4;
  if (score >= 65) return 3;
  if (score >= 40) return 2;
  if (score >= 15) return 1;
  return 0;
}

const SEG_COLOR = [
  "bg-success", "bg-emerald-400", "bg-warning", "bg-orange-500", "bg-danger",
];
const TEXT_COLOR = [
  "text-success", "text-emerald-400", "text-warning", "text-orange-500", "text-danger",
];

/** Live "fraud pressure" 0-100 with the 5 risk categories as a lit segment bar. */
export function RiskScore({ score }: { score: number }) {
  const idx = categoryOf(score);

  return (
    <div className="flex h-full flex-col justify-between">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Risk score
          </p>
          <motion.p
            key={score}
            initial={{ opacity: 0.5, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("mt-1 text-5xl font-bold tabular-nums", TEXT_COLOR[idx])}
          >
            {score}
            <span className="text-lg font-medium text-muted-foreground">/100</span>
          </motion.p>
        </div>
        <span className={cn("rounded-full bg-muted px-3 py-1 text-sm font-semibold", TEXT_COLOR[idx])}>
          {CATEGORIES[idx]}
        </span>
      </div>

      <div className="mt-5">
        <div className="flex gap-1.5">
          {CATEGORIES.map((cat, i) => (
            <div key={cat} className="flex-1">
              <motion.div
                className={cn("h-2 rounded-full transition-colors",
                  i <= idx ? SEG_COLOR[i] : "bg-muted")}
                initial={{ scaleX: 0.6, opacity: 0.5 }}
                animate={{ scaleX: 1, opacity: 1 }}
                transition={{ delay: i * 0.05 }}
              />
              <p className={cn("mt-1.5 text-center text-[10px] font-medium",
                i === idx ? TEXT_COLOR[idx] : "text-muted-foreground")}>
                {cat}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
