"use client";

import { motion, MotionConfig } from "framer-motion";
import {
  Activity, Play, Square, FileText, Bell, MessageSquare,
  CreditCard, ShieldAlert, PieChart, TrendingUp, MapPin, Download,
} from "lucide-react";
import { api } from "@/lib/api";
import { useLiveData } from "@/lib/live-provider";
import type { EngineAlert } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { cn, downloadCsv } from "@/lib/utils";
import { SecurityScore } from "./security-score";
import { RiskScore } from "./risk-score";
import { StatTiles } from "./stat-tiles";
import { FraudTimeline } from "./fraud-timeline";
import { ThreatHeatmap } from "./threat-heatmap";
import { AlertsFeed } from "./alerts-feed";
import { ActivityFeed } from "./activity-feed";
import { FraudTrend } from "./fraud-trend";
import { ThreatAnalytics } from "./threat-analytics";
import { RecentMessages } from "./recent-messages";
import { RecentTransactions } from "./recent-transactions";

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.16, 1, 0.3, 1] as const } },
};

function Section({
  title, icon: Icon, badge, className, contentClass, children,
}: {
  title: string;
  icon: typeof Activity;
  badge?: string;
  className?: string;
  contentClass?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("card flex h-full flex-col", className)}>
      <div className="card-h">
        <h3 className="flex items-center gap-2">
          <Icon className="size-4" style={{ color: "var(--brand-600)" }} aria-hidden />
          {title}
        </h3>
        {badge ? <span className="chip" style={{ background: "var(--surface-2)", color: "var(--muted-hex)" }}>{badge}</span> : null}
      </div>
      <div className={cn("flex-1 p-5", contentClass)}>{children}</div>
    </div>
  );
}

export function FraudDashboard() {
  // State + demo toggle come from the app-wide live provider. The demo is
  // client-side only, so switching it on or off never affects any other user;
  // exiting the demo instantly returns to the real (default) live state.
  const { state, connected, demo, setDemo } = useLiveData();

  const sendFeedback = async (alert: EngineAlert, label: "Safe" | "Scam") => {
    try { await api.sendFeedback(alert.ref_id, label); } catch { /* SSE reconciles */ }
  };

  const exportCsv = () => {
    if (!state) return;
    const rows = [
      ...state.recent_messages.map((m) => ({
        type: "message", label: m.label, probability: m.probability,
        region: m.region, detail: m.text, ts: m.ts,
      })),
      ...state.recent_transactions.map((t) => ({
        type: "transaction", label: t.decision, probability: t.probability,
        region: t.region, detail: `${t.bank ?? ""} NGN${Math.round(t.amount)}`.trim(), ts: t.ts,
      })),
      ...state.alerts.map((a) => ({
        type: `alert:${a.kind}`, label: a.severity, probability: a.probability,
        region: a.region, detail: a.title, ts: a.ts,
      })),
    ];
    downloadCsv(`nogree-live-${new Date().toISOString().slice(0, 10)}.csv`, rows);
  };

  const s = state;

  return (
    <MotionConfig reducedMotion="user">
      {/* Control bar */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <span className="livebadge" role="status" aria-live="polite"
          style={demo ? { background: "var(--med-t)", color: "var(--med)" } : undefined}>
          <span className={cn("dot-live", !connected && !demo && "opacity-60")} />
          <span>{demo ? "Demo mode - sample data (only you see this)" : connected ? "Live - updating automatically" : "Connecting…"}</span>
          {s && !demo ? <span style={{ opacity: 0.7 }}>· {s.live_subscribers} watching</span> : null}
        </span>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="head-btn" onClick={exportCsv}
            disabled={!s || (s.recent_messages.length + s.recent_transactions.length + s.alerts.length === 0)}
            aria-label="Download data as CSV">
            <Download /> Download CSV
          </button>
          {demo ? (
            <button className="head-btn" onClick={() => setDemo(false)} aria-label="Exit demo, back to live">
              <Square /> Exit demo
            </button>
          ) : (
            <button className="head-btn primary" onClick={() => setDemo(true)} aria-label="Start demo">
              <Play /> Start live demo
            </button>
          )}
        </div>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-4 lg:grid-cols-12"
      >
        {/* Hero: Security Score · Risk Score · Stats */}
        <motion.div variants={item} className="lg:col-span-3">
          <Card className="flex h-full items-center justify-center p-6">
            <SecurityScore score={s?.security_score ?? 100} grade={s?.security_grade ?? "A"} />
          </Card>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-3">
          <Card className="h-full p-6">
            <RiskScore score={s?.risk_score ?? 0} />
          </Card>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-6">
          {s ? <StatTiles stats={s.stats} /> : <div className="h-full min-h-[160px] rounded-2xl bg-muted/40 animate-pulse" />}
        </motion.div>

        {/* Report banner */}
        {s?.report ? (
          <motion.div variants={item} className="lg:col-span-12">
            <Card className="flex items-start gap-3 p-4">
              <FileText className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Daily security report · auto-generated
                </p>
                <p className="mt-1 text-sm text-foreground/90">{s.report.headline}</p>
              </div>
            </Card>
          </motion.div>
        ) : null}

        {/* Timeline + Heatmap */}
        <motion.div variants={item} className="lg:col-span-8">
          <Section title="Threat timeline" icon={Activity} badge="live">
            <FraudTimeline data={s?.timeline ?? []} />
          </Section>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Threat heatmap" icon={MapPin} badge="by region">
            <ThreatHeatmap cells={s?.heatmap ?? []} />
          </Section>
        </motion.div>

        {/* Fraud Trend · Threat Analytics · Notifications */}
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Fraud trend" icon={TrendingUp}>
            <FraudTrend data={s?.timeline ?? []} />
          </Section>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Threat analytics" icon={PieChart}>
            <ThreatAnalytics analytics={s?.analytics ?? { messages: { Scam: 0, Suspicious: 0, Safe: 0 }, transactions: { decline: 0, review: 0, approve: 0 } }} />
          </Section>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Notifications" icon={Bell} badge="auto" contentClass="max-h-[260px] overflow-y-auto">
            <ActivityFeed items={s?.activity ?? []} />
          </Section>
        </motion.div>

        {/* Recent Messages · Recent Transactions · Latest Alerts */}
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Recent messages" icon={MessageSquare} contentClass="max-h-[340px] overflow-y-auto">
            <RecentMessages messages={s?.recent_messages ?? []} />
          </Section>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Recent transactions" icon={CreditCard} contentClass="max-h-[340px] overflow-y-auto">
            <RecentTransactions transactions={s?.recent_transactions ?? []} />
          </Section>
        </motion.div>
        <motion.div variants={item} className="lg:col-span-4">
          <Section title="Latest alerts" icon={ShieldAlert} contentClass="max-h-[340px] overflow-y-auto">
            <AlertsFeed alerts={s?.alerts ?? []} onFeedback={sendFeedback} />
          </Section>
        </motion.div>
      </motion.div>

      {!demo && s && s.stats.messages_scanned === 0 ? (
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="mt-4 rounded-xl border border-dashed border-border/70 py-4 text-center text-sm text-muted-foreground"
        >
          Press <span className="font-medium text-foreground">Start live demo</span> to preview the
          engine with sample data. It is only visible to you and does not affect other accounts.
        </motion.p>
      ) : null}
    </MotionConfig>
  );
}
