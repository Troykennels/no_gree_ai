// Client-side demo state. Purely local to the browser: toggling "demo" on shows
// this populated snapshot; toggling off returns to the real live state. It never
// touches the server, so it is per-user and does not affect anyone else.

import type {
  AutomationState,
  EngineAlert,
  RecentMessage,
  RecentTransaction,
  TimelinePoint,
} from "./types";

const ago = (mins: number) => new Date(Date.now() - mins * 60_000).toISOString();

function timeline(): TimelinePoint[] {
  const safe = [6, 9, 7, 12, 10, 15, 13, 18, 14, 21, 17, 24, 19, 22];
  const threats = [1, 2, 1, 3, 2, 3, 2, 4, 3, 5, 3, 6, 4, 4];
  return safe.map((s, i) => {
    const d = new Date(Date.now() - (safe.length - 1 - i) * 5 * 60_000);
    const t = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    return { t, safe: s, threats: threats[i] };
  });
}

const HEATMAP = [
  { region: "Lagos", total: 214, threats: 38, level: "high" as const },
  { region: "Abuja", total: 148, threats: 22, level: "high" as const },
  { region: "Port Harcourt", total: 109, threats: 14, level: "medium" as const },
  { region: "Ibadan", total: 76, threats: 9, level: "medium" as const },
  { region: "Kano", total: 55, threats: 4, level: "medium" as const },
  { region: "Enugu", total: 34, threats: 2, level: "low" as const },
];

const RECENT_MESSAGES: RecentMessage[] = [
  { id: "m1", channel: "sms", text: "Your GTBank account will be BLOCKED. Update your BVN now via http://gtb-verify.top", label: "Scam", probability: 0.96, region: "Lagos", is_threat: true, ts: ago(2) },
  { id: "m2", channel: "whatsapp", text: "CONGRATULATIONS! You won N2,000,000 in the MTN promo. Send your BVN to claim.", label: "Scam", probability: 0.93, region: "Abuja", is_threat: true, ts: ago(9) },
  { id: "m3", channel: "sms", text: "Pre-approved instant loan of N150,000, no collateral. Pay a small fee: bit.ly/loan-ng", label: "Suspicious", probability: 0.58, region: "Ibadan", is_threat: true, ts: ago(18) },
  { id: "m4", channel: "sms", text: "Moniepoint: You received NGN12,000 from NGOZI EZE. Bal:NGN51,200.", label: "Safe", probability: 0.04, region: "Port Harcourt", is_threat: false, ts: ago(31) },
];

const RECENT_TRANSACTIONS: RecentTransaction[] = [
  { id: "t1", amount: 480000, bank: "Transfer to new payee", payer: "Unknown device", decision: "decline", probability: 0.91, risk_band: "critical", region: "Lagos", is_threat: true, ts: ago(3) },
  { id: "t2", amount: 95000, bank: "POS withdrawal", payer: "3rd attempt in 5 min", decision: "review", probability: 0.57, risk_band: "elevated", region: "Abuja", is_threat: true, ts: ago(11) },
  { id: "t3", amount: 1850000, bank: "Cross-border transfer", payer: "Lagos -> Cotonou", decision: "decline", probability: 0.88, risk_band: "high", region: "Lagos", is_threat: true, ts: ago(24) },
  { id: "t4", amount: 6500, bank: "POS - Shoprite Ikeja", payer: "GTBank verve", decision: "approve", probability: 0.03, risk_band: "minimal", region: "Lagos", is_threat: false, ts: ago(29) },
  { id: "t5", amount: 2000, bank: "Airtime top-up - MTN", payer: "Recurring", decision: "approve", probability: 0.02, risk_band: "minimal", region: "Enugu", is_threat: false, ts: ago(38) },
];

const ALERTS: EngineAlert[] = [
  { id: "a1", ref_id: "t1", kind: "transaction", severity: "critical", title: "Fraudulent transaction blocked", detail: "New payee, unknown device - NGN480,000 declined.", probability: 0.91, region: "Lagos", amount: 480000, status: "new", feedback: null, ts: ago(3) },
  { id: "a2", ref_id: "m1", kind: "message", severity: "critical", title: "Scam SMS detected", detail: "Fake GTBank BVN-update link.", probability: 0.96, region: "Lagos", amount: null, status: "new", feedback: null, ts: ago(2) },
  { id: "a3", ref_id: "t2", kind: "transaction", severity: "warning", title: "Transaction needs review", detail: "3rd POS attempt in 5 minutes.", probability: 0.57, region: "Abuja", amount: 95000, status: "new", feedback: null, ts: ago(11) },
];

/** A fresh, populated demo state (timestamps relative to now). */
export function makeDemoState(): AutomationState {
  return {
    stats: {
      messages_scanned: 128,
      transactions_analyzed: 96,
      scams_detected: 34,
      frauds_blocked: 47,
      alerts: 6,
      value_protected: 1_840_000,
      feedback_count: 12,
    },
    security_score: 78,
    security_grade: "C",
    risk_score: 42,
    timeline: timeline(),
    heatmap: HEATMAP,
    alerts: ALERTS,
    activity: RECENT_MESSAGES.map((m) => ({
      id: "act-" + m.id, kind: "message" as const, label: `${m.label} message from ${m.region}`,
      probability: m.probability, is_threat: m.is_threat, region: m.region, ts: m.ts,
    })),
    recent_messages: RECENT_MESSAGES,
    recent_transactions: RECENT_TRANSACTIONS,
    analytics: {
      messages: { Scam: 34, Suspicious: 18, Safe: 76 },
      transactions: { decline: 12, review: 9, approve: 75 },
    },
    report: {
      id: "demo-report",
      generated_at: ago(5),
      period: "rolling-24h",
      security_score: 78,
      security_grade: "C",
      totals: {
        messages_scanned: 128, transactions_analyzed: 96, scams_detected: 34,
        frauds_blocked: 47, alerts: 6, value_protected: 1_840_000, feedback_count: 12,
      },
      top_threat_regions: [
        { region: "Lagos", threats: 38, total: 214 },
        { region: "Abuja", threats: 22, total: 148 },
        { region: "Port Harcourt", threats: 14, total: 109 },
      ],
      critical_alerts: 2,
      headline: "34 scams and 47 fraudulent transactions stopped; N1,840,000 protected. Security score 78/100 (C).",
    },
    live_subscribers: 1,
    uptime_seconds: 4200,
    updated_at: new Date().toISOString(),
  };
}
