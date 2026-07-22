"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";
import type { RiskBand, Scan } from "@/lib/types";
import { RISK_THEME } from "@/lib/risk";

const ORDER: RiskBand[] = ["minimal", "low", "elevated", "high", "critical"];
const SHORT: Record<RiskBand, string> = {
  minimal: "Safe",
  low: "Low",
  elevated: "Susp.",
  high: "High",
  critical: "Crit.",
};

export function RiskDistributionChart({ scans }: { scans: Scan[] }) {
  const counts = ORDER.map((band) => ({
    band,
    label: SHORT[band],
    count: scans.filter((s) => s.assessment.risk_band === band).length,
    fill: RISK_THEME[band].hsl,
  }));

  const hasData = scans.length > 0;

  if (!hasData) {
    return (
      <div className="grid h-[220px] place-items-center text-sm text-muted-foreground">
        Run some scans to see your risk breakdown.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={counts} margin={{ top: 8, right: 4, left: 4, bottom: 0 }}>
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
        />
        <Tooltip
          cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 12,
            fontSize: 12,
          }}
          labelStyle={{ color: "hsl(var(--foreground))" }}
        />
        <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={44}>
          {counts.map((c) => (
            <Cell key={c.band} fill={c.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
