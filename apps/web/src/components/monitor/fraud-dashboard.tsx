"use client";

import { useState } from "react";
import { motion, MotionConfig } from "framer-motion";
import {
  Activity, Play, Square, FileText, Sparkles, Bell, MessageSquare,
  CreditCard, ShieldAlert, PieChart, TrendingUp, MapPin,
} from "lucide-react";
import { api } from "@/lib/api";
import { useLiveData } from "@/lib/live-provider";
import type { EngineAlert } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
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
    <Card className={cn("flex flex-col p-5", className)}>
      <div className="mb-4 flex items-center gap-2">
        <Icon className="size-4 text-primary" aria-hidden />
        <h2 className="text-sm font-semibold">{title}</h2>
        {badge ? <Badge variant="outline" className="ml-auto">{badge}</Badge> : null}
      </div>
      <div className={cn("flex-1", contentClass)}>{children}</div>
    </Card>
  );
}

export function FraudDashboard() {
  const [simRunning, setSimRunning] = useState(false);
  const [busy, setBusy] = useState(false);

  // State + notifications come from the app-wide live provider (single SSE);
  // toasts and the notification center are handled globally.
  const { state, connected } = useLiveData();

  const startDemo = async () => {
    setBusy(true);
    try { await api.simulate(60, 800); setSimRunning(true); } catch { /* badge shows status */ }
    finally { setBusy(false); }
  };
  const stopDemo = async () => {
    setBusy(true);
    try { await api.simulateStop(); } finally { setSimRunning(false); setBusy(false); }
  };
  const sendFeedback = async (alert: EngineAlert, label: "Safe" | "Scam") => {
    try { await api.sendFeedback(alert.ref_id, label); } catch { /* SSE reconciles */ }
  };

  const s = state;

  return (
    <MotionConfig reducedMotion="user">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-grid size-8 place-items-center rounded-xl bg-primary/10">
              <Sparkles className="size-4 text-primary" aria-hidden />
            </span>
            <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
              Fraud Intelligence
            </h1>
          </div>
          <p className="mt-1.5 flex items-center gap-2 text-sm text-muted-foreground"
            role="status" aria-live="polite">
            <span className="inline-flex items-center gap-1.5">
              <span className={cn("relative flex size-2")}>
                <span className={cn("absolute inline-flex size-full rounded-full opacity-75",
                  connected ? "animate-ping bg-success" : "bg-muted-foreground")} />
                <span className={cn("relative inline-flex size-2 rounded-full",
                  connected ? "bg-success" : "bg-muted-foreground")} />
              </span>
              {connected ? "Live — updating automatically" : "Connecting…"}
            </span>
            {s ? <span className="text-muted-foreground/70">· {s.live_subscribers} watching</span> : null}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {simRunning ? (
            <Button variant="outline" size="sm" onClick={stopDemo} disabled={busy}
              aria-label="Stop live demo">
              <Square /> Stop demo
            </Button>
          ) : (
            <Button size="sm" onClick={startDemo} disabled={busy} aria-label="Start live demo">
              <Play /> Start live demo
            </Button>
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

      {!simRunning && s && s.stats.messages_scanned === 0 ? (
        <motion.p
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="mt-4 rounded-xl border border-dashed border-border/70 py-4 text-center text-sm text-muted-foreground"
        >
          Press <span className="font-medium text-foreground">Start live demo</span> to watch the
          engine score messages and transactions in real time — nothing here needs a refresh.
        </motion.p>
      ) : null}
    </MotionConfig>
  );
}
