"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  CreditCard,
  Download,
  ScanLine,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { api, ApiError } from "@/lib/api";
import { useLiveData } from "@/lib/live-provider";
import { downloadCsv } from "@/lib/utils";
import type { HeatCell, RecentTransaction, TimelinePoint } from "@/lib/types";

const naira = (n: number) =>
  "₦" + Math.round(n).toLocaleString("en-NG");

function timeAgo(ts: string): string {
  const s = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (Number.isNaN(s)) return "";
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function DashboardPage() {
  const router = useRouter();
  const { state, connected, demo, setDemo } = useLiveData();

  const meQuery = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });

  useEffect(() => {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      router.replace("/login");
    }
  }, [meQuery.error, router]);

  const s = state?.stats;
  const firstName = meQuery.data?.full_name?.split(" ")[0];

  function exportCsv() {
    const rows = state?.recent_transactions ?? [];
    downloadCsv(
      `nogree-transactions-${new Date().toISOString().slice(0, 10)}.csv`,
      rows.map((t) => ({
        time: t.ts,
        bank: t.bank ?? "",
        amount: t.amount,
        decision: t.decision,
        fraud_probability: t.probability,
        risk_band: t.risk_band,
        region: t.region,
      })),
    );
  }

  return (
    <AppShell>
      <div className="page-head">
        <div>
          <h1>{firstName ? `Welcome back, ${firstName}` : "Fraud Intelligence"}</h1>
          <p>Your live fraud picture - updated in real time as messages and transactions are scored.</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="head-btn" onClick={exportCsv} disabled={!state?.recent_transactions?.length}>
            <Download /> Download CSV
          </button>
          <Link href="/detector" className="head-btn primary">
            <ScanLine /> New scan
          </Link>
        </div>
      </div>

      {demo && (
        <div className="card pad" style={{ marginBottom: 18, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, background: "var(--med-t)", borderColor: "var(--med)" }}>
          <span style={{ color: "var(--med)", fontWeight: 600, fontSize: 13 }}>
            Demo mode - showing sample data. Only you see this; it does not affect other accounts.
          </span>
          <button className="head-btn" onClick={() => setDemo(false)}>Exit demo</button>
        </div>
      )}

      {!state ? (
        <DashboardSkeleton />
      ) : (
        <div className="grid cols-12">
          {/* KPI ROW */}
          <div className="span-3">
            <Kpi
              icon={<ScanLine />}
              tint="var(--brand)"
              bg="var(--brand-tint)"
              label="Messages scanned"
              value={s!.messages_scanned}
              chip={`${s!.scams_detected} scams`}
              kind={s!.scams_detected > 0 ? "down" : "up"}
            />
          </div>
          <div className="span-3">
            <Kpi
              icon={<CreditCard />}
              tint="var(--med)"
              bg="var(--med-t)"
              label="Transactions analysed"
              value={s!.transactions_analyzed}
              chip={`${s!.frauds_blocked} blocked`}
              kind={s!.frauds_blocked > 0 ? "down" : "up"}
            />
          </div>
          <div className="span-3">
            <Kpi
              icon={<ShieldCheck />}
              tint="var(--safe)"
              bg="var(--safe-t)"
              label="Value protected"
              value={naira(s!.value_protected)}
              chip="protected"
              kind="up"
            />
          </div>
          <div className="span-3">
            <Kpi
              icon={<AlertTriangle />}
              tint="var(--crit)"
              bg="var(--crit-t)"
              label="Active alerts"
              value={s!.alerts}
              chip={s!.alerts > 0 ? "needs review" : "all clear"}
              kind={s!.alerts > 0 ? "down" : "up"}
            />
          </div>

          {/* SECURITY GAUGE */}
          <div className="span-4">
            <div className="card">
              <ScoreCard score={state.security_score} grade={state.security_grade} live={connected} />
            </div>
          </div>

          {/* TREND CHART */}
          <div className="span-8">
            <div className="card">
              <div className="card-h">
                <h3>Threat activity</h3>
                <div className="chart-legend">
                  <span><i className="lg-dot" style={{ background: "var(--brand)" }} /> Safe</span>
                  <span><i className="lg-dot" style={{ background: "var(--crit)" }} /> Threats</span>
                </div>
              </div>
              <div className="chart-body">
                <TrendChart timeline={state.timeline} />
              </div>
            </div>
          </div>

          {/* RECENT TRANSACTIONS */}
          <div className="span-7">
            <div className="card">
              <div className="card-h">
                <h3>Recent transactions</h3>
                <Link href="/transaction" className="link">Score a transaction →</Link>
              </div>
              {state.recent_transactions.length === 0 ? (
                <Empty text="No transactions scored yet." />
              ) : (
                state.recent_transactions.slice(0, 6).map((t) => <TxnRow key={t.id} t={t} />)
              )}
            </div>
          </div>

          {/* HEATMAP */}
          <div className="span-5">
            <div className="card">
              <div className="card-h">
                <h3>Threat heatmap</h3>
                <span style={{ fontSize: 12, color: "var(--muted-hex)" }}>by region</span>
              </div>
              <div style={{ padding: "8px 0 12px" }}>
                {state.heatmap.length === 0 ? (
                  <Empty text="No regional data yet." />
                ) : (
                  <HeatMap cells={state.heatmap} />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <p className="footnote">
        No_Gree AI · Detect. Protect. Prevent. - {connected ? "Live protection active" : "Reconnecting to live feed…"}
      </p>
    </AppShell>
  );
}

/* ── KPI ─────────────────────────────────────────────────────────────────── */
function Kpi({
  icon, tint, bg, label, value, chip, kind,
}: {
  icon: React.ReactNode; tint: string; bg: string;
  label: string; value: number | string; chip: string; kind: "up" | "down";
}) {
  return (
    <div className="card pad kpi kpi-card">
      <div className="top">
        <span className="ico" style={{ background: bg, color: tint }}>{icon}</span>
        <span className={`delta ${kind}`}>
          {kind === "up" ? <TrendingUp /> : <TrendingDown />}
          {chip}
        </span>
      </div>
      <div>
        <div className="label">{label}</div>
        <div className="val num">{value}</div>
      </div>
    </div>
  );
}

/* ── SECURITY GAUGE ──────────────────────────────────────────────────────── */
function ScoreCard({ score, grade, live }: { score: number; grade: string; live: boolean }) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const R = 78;
  const C = 2 * Math.PI * R;
  const dash = (clamped / 100) * C;
  const color =
    clamped >= 80 ? "var(--safe)" : clamped >= 60 ? "var(--med)" : clamped >= 40 ? "var(--high)" : "var(--crit)";
  const status =
    clamped >= 80 ? { cls: "c-safe", label: "Strong" }
    : clamped >= 60 ? { cls: "c-med", label: "Fair" }
    : clamped >= 40 ? { cls: "c-high", label: "At risk" }
    : { cls: "c-crit", label: "Critical" };

  return (
    <div className="score-card">
      <p className="eyebrow">Security score</p>
      <div className="gauge-wrap">
        <svg width="184" height="184" viewBox="0 0 184 184">
          <circle className="track" cx="92" cy="92" r={R} fill="none" strokeWidth="14" />
          <circle
            cx="92" cy="92" r={R} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"
            strokeDasharray={`${dash} ${C - dash}`}
            style={{ transition: "stroke-dasharray .6s cubic-bezier(.2,.75,.25,1)" }}
          />
        </svg>
        <div className="gauge-center">
          <span className="g-num">{clamped}</span>
          <span className="g-of">Grade {grade}</span>
        </div>
      </div>
      <span className={`status-chip ${status.cls}`}>
        <span className="d" style={{ background: color }} /> {status.label}
      </span>
      <p className="score-note">
        {live ? "Live protection active." : "Reconnecting…"} This score reflects current fraud pressure across all monitored channels.
      </p>
    </div>
  );
}

/* ── TREND CHART (custom SVG, hover tooltip) ─────────────────────────────── */
function TrendChart({ timeline }: { timeline: TimelinePoint[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 720, H = 220, PAD = 10;
  const pts = timeline.length ? timeline : [];

  const geo = useMemo(() => {
    if (!pts.length) return null;
    const maxV = Math.max(1, ...pts.map((p) => Math.max(p.threats, p.safe)));
    const x = (i: number) => PAD + (i / Math.max(1, pts.length - 1)) * (W - PAD * 2);
    const y = (v: number) => H - PAD - (v / maxV) * (H - PAD * 2);
    const line = (key: "threats" | "safe") =>
      pts.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
    const area = `${line("safe")} L${x(pts.length - 1).toFixed(1)},${H - PAD} L${x(0).toFixed(1)},${H - PAD} Z`;
    return { x, y, line, area, maxV };
  }, [pts]);

  if (!geo) return <Empty text="No activity data yet." />;

  return (
    <div style={{ position: "relative" }}>
      <svg
        viewBox={`0 0 ${W} ${H}`} width="100%" height="220" preserveAspectRatio="none"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
          const rel = ((e.clientX - rect.left) / rect.width) * W;
          const i = Math.round(((rel - PAD) / (W - PAD * 2)) * (pts.length - 1));
          setHover(Math.max(0, Math.min(pts.length - 1, i)));
        }}
        style={{ cursor: "crosshair", display: "block" }}
      >
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1={PAD} x2={W - PAD} y1={PAD + f * (H - PAD * 2)} y2={PAD + f * (H - PAD * 2)}
            stroke="var(--track)" strokeWidth="1" />
        ))}
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={geo.area} fill="url(#areaFill)" />
        <path d={geo.line("safe")} fill="none" stroke="var(--brand)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d={geo.line("threats")} fill="none" stroke="var(--crit)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {hover !== null && (
          <>
            <line x1={geo.x(hover)} x2={geo.x(hover)} y1={PAD} y2={H - PAD} stroke="var(--brand)" strokeWidth="1" strokeDasharray="4 4" opacity="0.5" />
            <circle cx={geo.x(hover)} cy={geo.y(pts[hover].safe)} r="4" fill="var(--surface)" stroke="var(--brand)" strokeWidth="2" />
            <circle cx={geo.x(hover)} cy={geo.y(pts[hover].threats)} r="4" fill="var(--surface)" stroke="var(--crit)" strokeWidth="2" />
          </>
        )}
      </svg>
      {hover !== null && (
        <div
          className="chart-tip"
          style={{ left: `${(geo.x(hover) / W) * 100}%`, top: `${(geo.y(pts[hover].threats) / H) * 100}%`, opacity: 1 }}
        >
          <div className="lab">{pts[hover].t}</div>
          {pts[hover].threats} threats · {pts[hover].safe} safe
        </div>
      )}
    </div>
  );
}

/* ── TRANSACTION ROW ─────────────────────────────────────────────────────── */
function TxnRow({ t }: { t: RecentTransaction }) {
  const chip =
    t.decision === "decline" ? "c-crit" : t.decision === "review" ? "c-med" : "c-safe";
  const iconBg =
    t.decision === "decline" ? "var(--crit-t)" : t.decision === "review" ? "var(--med-t)" : "var(--safe-t)";
  const iconColor =
    t.decision === "decline" ? "var(--crit)" : t.decision === "review" ? "var(--med)" : "var(--safe)";
  return (
    <div className="row">
      <span className="r-ico" style={{ background: iconBg, color: iconColor }}>
        <CreditCard />
      </span>
      <div className="r-main">
        <div className="t">{t.bank ?? "Card transaction"}{t.payer ? ` · ${t.payer}` : ""}</div>
        <div className="s">{t.region} · {timeAgo(t.ts)}</div>
      </div>
      <div className="r-end">
        <span className="amt num">{naira(t.amount)}</span>
        <span className={`chip ${chip}`}><span className="d" /> {t.decision}</span>
      </div>
    </div>
  );
}

/* ── HEATMAP ─────────────────────────────────────────────────────────────── */
function HeatMap({ cells }: { cells: HeatCell[] }) {
  const max = Math.max(1, ...cells.map((c) => c.total));
  const color = (lvl: HeatCell["level"]) =>
    lvl === "high" ? "var(--crit)" : lvl === "medium" ? "var(--high)" : "var(--safe)";
  return (
    <>
      {cells.slice(0, 7).map((c) => (
        <div className="heat-row" key={c.region}>
          <span className="city">{c.region}</span>
          <span className="heat-bar">
            <i style={{ width: `${Math.max(6, (c.total / max) * 100)}%`, background: color(c.level) }} />
          </span>
          <span className="n num">{c.threats}</span>
        </div>
      ))}
    </>
  );
}

/* ── HELPERS ─────────────────────────────────────────────────────────────── */
function Empty({ text }: { text: string }) {
  return (
    <div style={{ display: "grid", placeItems: "center", gap: 10, padding: "36px 20px", textAlign: "center" }}>
      <Activity style={{ width: 26, height: 26, color: "var(--muted-hex)" }} />
      <p style={{ fontSize: 13, color: "var(--muted-hex)" }}>{text}</p>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid cols-12">
      {Array.from({ length: 4 }).map((_, i) => (
        <div className="span-3" key={i}><div className="sk" style={{ height: 108 }}><div className="sk-c"><div className="sk-pill" style={{ width: "60%" }} /></div></div></div>
      ))}
      <div className="span-4"><div className="sk" style={{ height: 320 }}><div className="sk-c"><div className="sk-circle" /></div></div></div>
      <div className="span-8"><div className="sk" style={{ height: 320 }} /></div>
      <div className="span-7"><div className="sk" style={{ height: 300 }} /></div>
      <div className="span-5"><div className="sk" style={{ height: 300 }} /></div>
    </div>
  );
}
