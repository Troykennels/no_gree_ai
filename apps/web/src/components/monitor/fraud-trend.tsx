"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { TimelinePoint } from "@/lib/types";
import { cn } from "@/lib/utils";

function label(t: string): string {
  return new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function FraudTrend({ data }: { data: TimelinePoint[] }) {
  const series = data.map((p) => ({ ...p, label: label(p.t) }));
  const totalThreats = series.reduce((s, p) => s + p.threats, 0);

  // Trend delta: recent half vs earlier half.
  const half = Math.floor(series.length / 2);
  const earlier = series.slice(0, half).reduce((s, p) => s + p.threats, 0);
  const recent = series.slice(half).reduce((s, p) => s + p.threats, 0);
  const delta = recent - earlier;
  const Trend = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  const trendColor = delta > 0 ? "text-danger" : delta < 0 ? "text-success" : "text-muted-foreground";

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 flex items-end justify-between">
        <div>
          <p className="text-3xl font-bold tabular-nums">{totalThreats}</p>
          <p className="text-xs text-muted-foreground">threats detected</p>
        </div>
        <span className={cn("flex items-center gap-1 text-sm font-semibold", trendColor)}>
          <Trend className="size-4" />
          {delta > 0 ? "+" : ""}{delta}
        </span>
      </div>
      {series.length === 0 ? (
        <div className="grid flex-1 place-items-center text-sm text-muted-foreground">
          Waiting for activity…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={series} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <XAxis dataKey="label" hide />
            <Tooltip
              cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
              contentStyle={{
                background: "hsl(var(--card))", border: "1px solid hsl(var(--border))",
                borderRadius: 12, fontSize: 12,
              }}
              labelStyle={{ color: "hsl(var(--foreground))" }}
            />
            <Bar dataKey="threats" radius={[4, 4, 0, 0]} maxBarSize={20} isAnimationActive
              animationDuration={500}>
              {series.map((p, i) => (
                <Cell key={i} fill={p.threats > 0 ? "hsl(0 84% 60%)" : "hsl(var(--muted))"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
