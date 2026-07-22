"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import type { Analytics } from "@/lib/types";
import { cn } from "@/lib/utils";

const MSG_COLORS: Record<string, string> = {
  Scam: "hsl(0 84% 60%)",
  Suspicious: "hsl(38 92% 50%)",
  Safe: "hsl(158 84% 42%)",
};

export function ThreatAnalytics({ analytics }: { analytics: Analytics }) {
  const msg = analytics.messages;
  const data = [
    { name: "Scam", value: msg.Scam },
    { name: "Suspicious", value: msg.Suspicious },
    { name: "Safe", value: msg.Safe },
  ];
  const total = data.reduce((s, d) => s + d.value, 0);
  const txn = analytics.transactions;

  return (
    <div className="flex h-full flex-col">
      <div className="relative mx-auto" style={{ width: 168, height: 168 }}>
        {total > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" innerRadius={54} outerRadius={78}
                paddingAngle={3} stroke="none" isAnimationActive animationDuration={600}>
                {data.map((d) => <Cell key={d.name} fill={MSG_COLORS[d.name]} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="grid h-full place-items-center rounded-full border-8 border-muted" />
        )}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold tabular-nums">{total}</span>
          <span className="text-[11px] text-muted-foreground">messages</span>
        </div>
      </div>

      <div className="mt-3 flex justify-center gap-3">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full" style={{ background: MSG_COLORS[d.name] }} />
            <span className="text-xs text-muted-foreground">{d.name} {d.value}</span>
          </div>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border/60 pt-3">
        {([["Approve", txn.approve, "text-success"], ["Review", txn.review, "text-warning"],
           ["Decline", txn.decline, "text-danger"]] as const).map(([label, value, color]) => (
          <div key={label} className="text-center">
            <p className={cn("text-lg font-bold tabular-nums", color)}>{value}</p>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
