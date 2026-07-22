"use client";

import { motion } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

function scoreColor(score: number): string {
  if (score >= 80) return "hsl(158 84% 42%)";
  if (score >= 65) return "hsl(38 92% 50%)";
  if (score >= 50) return "hsl(25 95% 53%)";
  return "hsl(0 84% 60%)";
}

/** Auto-recalculated security score, 0–100, higher is safer. */
export function SecurityScore({ score, grade }: { score: number; grade: string }) {
  const size = 190;
  const stroke = 14;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke="hsl(var(--muted))" strokeWidth={stroke} />
          <motion.circle
            cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke={color} strokeWidth={stroke} strokeLinecap="round"
            strokeDasharray={c}
            initial={false}
            animate={{ strokeDashoffset: c * (1 - pct) }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            key={grade}
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-5xl font-bold tabular-nums"
            style={{ color }}
          >
            {grade}
          </motion.span>
          <span className="mt-1 text-2xl font-semibold tabular-nums text-foreground">
            {Math.round(score)}
          </span>
          <span className="text-xs uppercase tracking-wider text-muted-foreground">
            / 100
          </span>
        </div>
      </div>
      <div className={cn("mt-3 inline-flex items-center gap-1.5 text-sm font-medium")}
        style={{ color }}>
        <ShieldCheck className="size-4" /> Security score
      </div>
    </div>
  );
}
