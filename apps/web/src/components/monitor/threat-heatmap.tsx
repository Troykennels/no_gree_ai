"use client";

import { motion } from "framer-motion";
import type { HeatCell, HeatLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

const LEVEL: Record<HeatLevel, string> = {
  low: "bg-success/15 text-success border-success/20",
  medium: "bg-warning/15 text-warning border-warning/25",
  high: "bg-danger/15 text-danger border-danger/25",
};

export function ThreatHeatmap({ cells }: { cells: HeatCell[] }) {
  if (cells.length === 0) {
    return (
      <div className="grid h-[200px] place-items-center text-sm text-muted-foreground">
        No regional activity yet.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {cells.map((cell) => (
        <motion.div
          key={cell.region}
          layout
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className={cn(
            "rounded-xl border px-3 py-2.5 transition-colors",
            LEVEL[cell.level],
          )}
        >
          <div className="flex items-center justify-between">
            <span className="truncate text-sm font-semibold">{cell.region}</span>
            <span className="text-xs font-bold tabular-nums">{cell.threats}</span>
          </div>
          <p className="mt-0.5 text-[11px] opacity-80">
            {cell.total} events · {cell.level} risk
          </p>
        </motion.div>
      ))}
    </div>
  );
}
