"use client";

import { motion } from "framer-motion";
import type { RiskBand } from "@/lib/types";
import { riskTheme } from "@/lib/risk";

export function RiskGauge({
  probability,
  band,
  size = 200,
}: {
  probability: number;
  band: RiskBand;
  size?: number;
}) {
  const theme = riskTheme(band);
  const stroke = 14;
  const radius = (size - stroke) / 2;
  const circumference = Math.PI * radius; // semicircle
  const pct = Math.max(0, Math.min(1, probability));

  return (
    <div className="relative" style={{ width: size, height: size / 2 + 28 }}>
      <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(158 84% 42%)" />
            <stop offset="55%" stopColor="hsl(38 92% 50%)" />
            <stop offset="100%" stopColor="hsl(0 84% 60%)" />
          </linearGradient>
        </defs>
        {/* track */}
        <path
          d={`M ${stroke / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
            size - stroke / 2
          } ${size / 2}`}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* value */}
        <motion.path
          d={`M ${stroke / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${
            size - stroke / 2
          } ${size / 2}`}
          fill="none"
          stroke="url(#gaugeGrad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - pct) }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
        <motion.span
          className={`text-4xl font-bold tabular-nums ${theme.text}`}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          {Math.round(pct * 100)}%
        </motion.span>
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Fraud risk
        </span>
      </div>
    </div>
  );
}
