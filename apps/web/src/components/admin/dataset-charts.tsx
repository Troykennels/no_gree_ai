"use client";

import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const TOOLTIP = {
  background: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 12,
  fontSize: 12,
} as const;

export function ClassDistributionChart({
  data,
}: {
  data: { name: string; value: number; fill: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <XAxis
          dataKey="name"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={44}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
        />
        <Tooltip cursor={{ fill: "hsl(var(--muted) / 0.4)" }} contentStyle={TOOLTIP} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={64}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function RatioPie({
  data,
}: {
  data: { name: string; value: number; fill: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={45}
          outerRadius={75}
          paddingAngle={2}
        >
          {data.map((d) => (
            <Cell key={d.name} fill={d.fill} stroke="hsl(var(--card))" strokeWidth={2} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function CategoryChart({
  data,
}: {
  data: { name: string; value: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 26)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
      >
        <XAxis
          type="number"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={130}
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
        />
        <Tooltip cursor={{ fill: "hsl(var(--muted) / 0.4)" }} contentStyle={TOOLTIP} />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="hsl(var(--danger))" maxBarSize={18} />
      </BarChart>
    </ResponsiveContainer>
  );
}
