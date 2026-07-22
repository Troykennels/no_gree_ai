"use client";

import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimelinePoint } from "@/lib/types";

function label(t: string): string {
  const d = new Date(t);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function FraudTimeline({ data }: { data: TimelinePoint[] }) {
  const series = data.map((p) => ({ ...p, label: label(p.t) }));

  if (series.length === 0) {
    return (
      <div className="grid h-[240px] place-items-center text-sm text-muted-foreground">
        Waiting for live activity…
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={series} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(0 84% 60%)" stopOpacity={0.5} />
            <stop offset="100%" stopColor="hsl(0 84% 60%)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="safeGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(158 84% 42%)" stopOpacity={0.4} />
            <stop offset="100%" stopColor="hsl(158 84% 42%)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="label" tickLine={false} axisLine={false}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} minTickGap={24} />
        <YAxis tickLine={false} axisLine={false} width={34} allowDecimals={false}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
        <Tooltip
          contentStyle={{
            background: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 12, fontSize: 12,
          }}
          labelStyle={{ color: "hsl(var(--foreground))" }}
        />
        <Area type="monotone" dataKey="safe" stroke="hsl(158 84% 42%)" strokeWidth={2}
          fill="url(#safeGrad)" isAnimationActive animationDuration={500} name="Safe" />
        <Area type="monotone" dataKey="threats" stroke="hsl(0 84% 60%)" strokeWidth={2}
          fill="url(#threatGrad)" isAnimationActive animationDuration={500} name="Threats" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
