import type { RiskBand } from "./types";

export interface RiskTheme {
  band: RiskBand;
  label: string;
  // Tailwind tokens
  text: string;
  ring: string;
  bg: string;
  gradient: string;
  hsl: string; // for inline SVG / recharts
}

export const RISK_THEME: Record<RiskBand, RiskTheme> = {
  critical: {
    band: "critical",
    label: "Critical risk",
    text: "text-danger",
    ring: "ring-danger/30",
    bg: "bg-danger/10",
    gradient: "from-danger to-rose-500",
    hsl: "hsl(0 84% 60%)",
  },
  high: {
    band: "high",
    label: "High risk",
    text: "text-danger",
    ring: "ring-danger/30",
    bg: "bg-danger/10",
    gradient: "from-danger to-orange-500",
    hsl: "hsl(6 82% 60%)",
  },
  elevated: {
    band: "elevated",
    label: "Suspicious",
    text: "text-warning",
    ring: "ring-warning/30",
    bg: "bg-warning/10",
    gradient: "from-warning to-amber-400",
    hsl: "hsl(38 92% 50%)",
  },
  low: {
    band: "low",
    label: "Likely safe",
    text: "text-success",
    ring: "ring-success/30",
    bg: "bg-success/10",
    gradient: "from-success to-emerald-400",
    hsl: "hsl(158 84% 39%)",
  },
  minimal: {
    band: "minimal",
    label: "Safe",
    text: "text-success",
    ring: "ring-success/30",
    bg: "bg-success/10",
    gradient: "from-success to-emerald-400",
    hsl: "hsl(158 84% 42%)",
  },
};

export function riskTheme(band: RiskBand): RiskTheme {
  return RISK_THEME[band] ?? RISK_THEME.minimal;
}
