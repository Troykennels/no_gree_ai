"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2, CreditCard, CheckCircle2, AlertTriangle, XCircle, Radio, Zap, Send } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api, ApiError, tokenStore } from "@/lib/api";
import type { TransactionResult, TxnDecision } from "@/lib/types";

type Form = {
  TransactionAmt: string;
  ProductCD: string;
  card4: string;
  card6: string;
  P_emaildomain: string;
  C1: string;
  C13: string;
};

const PRESETS: { label: string; region: string; values: Partial<Form> }[] = [
  {
    label: "Everyday POS (₦6,500)",
    region: "Lagos",
    values: { TransactionAmt: "6500", ProductCD: "W", card4: "verve", card6: "debit", P_emaildomain: "gmail.com", C1: "1", C13: "1" },
  },
  {
    label: "High-risk transfer (₦1.85m)",
    region: "Lagos",
    values: { TransactionAmt: "1850000", ProductCD: "C", card4: "mastercard", card6: "credit", P_emaildomain: "outlook.com", C1: "48", C13: "62" },
  },
  {
    label: "Cross-border (₦480k)",
    region: "Abuja",
    values: { TransactionAmt: "480000", ProductCD: "C", card4: "visa", card6: "credit", P_emaildomain: "yahoo.com", C1: "22", C13: "31" },
  },
];

const PRODUCTS = ["W", "C", "R", "H", "S"];
const NETWORKS = ["verve", "visa", "mastercard"];
const CARD_TYPES = ["debit", "credit"];

const UI: Record<TxnDecision, { icon: typeof CheckCircle2; color: string; tint: string; chip: string }> = {
  approve: { icon: CheckCircle2, color: "var(--safe)", tint: "var(--safe-t)", chip: "c-safe" },
  review: { icon: AlertTriangle, color: "var(--med)", tint: "var(--med-t)", chip: "c-med" },
  decline: { icon: XCircle, color: "var(--crit)", tint: "var(--crit-t)", chip: "c-crit" },
};

const EMPTY: Form = {
  TransactionAmt: "", ProductCD: "W", card4: "verve", card6: "debit",
  P_emaildomain: "", C1: "", C13: "",
};

export function TransactionScorer() {
  const [form, setForm] = useState<Form>(EMPTY);
  const [region, setRegion] = useState("Lagos");
  const [autoScore, setAutoScore] = useState(true);
  const [authed, setAuthed] = useState(false);
  useEffect(() => setAuthed(!!tokenStore.get()), []);

  const buildFeatures = useCallback((): Record<string, number | string | null> => {
    const f: Record<string, number | string | null> = {};
    if (form.TransactionAmt) f.TransactionAmt = Number(form.TransactionAmt);
    if (form.ProductCD) f.ProductCD = form.ProductCD;
    if (form.card4) f.card4 = form.card4;
    if (form.card6) f.card6 = form.card6;
    if (form.P_emaildomain) f.P_emaildomain = form.P_emaildomain;
    if (form.C1) f.C1 = Number(form.C1);
    if (form.C13) f.C13 = Number(form.C13);
    return f;
  }, [form]);

  const mutation = useMutation<TransactionResult, Error, void>({
    mutationFn: () => api.scoreTransaction(buildFeatures()),
  });

  const ingest = useMutation<Record<string, unknown>, Error, void>({
    mutationFn: () => api.ingestTransaction(buildFeatures(), region),
  });

  // Automation: auto-score (debounced) whenever inputs change and auto-score is on.
  const scoreRef = useRef(mutation.mutate);
  scoreRef.current = mutation.mutate;
  useEffect(() => {
    if (!autoScore || !form.TransactionAmt) return;
    const t = setTimeout(() => scoreRef.current(), 650);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, autoScore]);

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    ingest.reset();
    setForm((f) => ({ ...f, [k]: e.target.value }));
  };

  const applyPreset = (p: (typeof PRESETS)[number]) => {
    ingest.reset();
    setRegion(p.region);
    setForm({ ...EMPTY, ...p.values });
    // Instant score on preset - feels automated.
    setTimeout(() => scoreRef.current(), 30);
  };

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The transaction-fraud model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the No Gree AI API. Is it running?"
        : null;

  const result = mutation.data;
  const ui = result ? UI[result.decision] : UI.approve;
  const Icon = ui.icon;
  const maxWeight = result ? Math.max(...result.factors.map((f) => Math.abs(f.weight)), 0.0001) || 1 : 1;
  const pct = result ? Math.round(result.fraud_probability * 100) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="card pad">
        <div style={{ marginBottom: 16, display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: "var(--muted-hex)" }}>Presets:</span>
          {PRESETS.map((p) => (
            <button key={p.label} className="sample" onClick={() => applyPreset(p)}>
              {p.label}
            </button>
          ))}
          <label className="remember" style={{ marginLeft: "auto", fontSize: 12.5 }} title="Re-score automatically as you edit">
            <input type="checkbox" checked={autoScore} onChange={(e) => setAutoScore(e.target.checked)} />
            <Zap style={{ width: 14, height: 14, color: autoScore ? "var(--brand-600)" : "var(--muted-hex)" }} /> Auto-score
          </label>
        </div>

        <div className="grid" style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
          <div>
            <label className="field-label" htmlFor="amt">Amount (₦)</label>
            <input id="amt" className="ng-input" type="number" inputMode="decimal" placeholder="e.g. 25000" value={form.TransactionAmt} onChange={set("TransactionAmt")} />
          </div>
          <div>
            <label className="field-label" htmlFor="email">Purchaser email domain</label>
            <input id="email" className="ng-input" placeholder="e.g. gmail.com" value={form.P_emaildomain} onChange={set("P_emaildomain")} />
          </div>
          <div>
            <label className="field-label" htmlFor="product">Product category</label>
            <select id="product" className="ng-select" value={form.ProductCD} onChange={set("ProductCD")}>
              {PRODUCTS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="network">Card network</label>
            <select id="network" className="ng-select" value={form.card4} onChange={set("card4")}>
              {NETWORKS.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div>
            <label className="field-label" htmlFor="ctype">Card type</label>
            <select id="ctype" className="ng-select" value={form.card6} onChange={set("card6")}>
              {CARD_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label className="field-label" htmlFor="c1">Activity C1</label>
              <input id="c1" className="ng-input" type="number" placeholder="opt." value={form.C1} onChange={set("C1")} />
            </div>
            <div>
              <label className="field-label" htmlFor="c13">Activity C13</label>
              <input id="c13" className="ng-input" type="number" placeholder="opt." value={form.C13} onChange={set("C13")} />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 18, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <p style={{ fontSize: 12, color: "var(--muted-hex)", display: "inline-flex", alignItems: "center", gap: 6 }}>
            {autoScore ? <><Radio style={{ width: 13, height: 13, color: "var(--brand-600)" }} /> Auto-scoring live - blank fields are imputed by the model.</> : "Any field left blank is imputed by the model."}
          </p>
          <button className="head-btn primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? <><Loader2 className="animate-spin" /> Scoring…</> : <><CreditCard /> Score transaction</>}
          </button>
        </div>

        {errorText && <p className="alert-error">{errorText}</p>}
      </div>

      {result && (
        <div className="card reveal in">
          <div className="result-head">
            <span className="ric" style={{ background: ui.tint, color: ui.color }}>
              <Icon />
            </span>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 700, color: ui.color, fontSize: 15, textTransform: "capitalize" }}>{result.decision}</p>
              <p style={{ fontSize: 12, color: "var(--muted-hex)" }}>
                <span style={{ textTransform: "capitalize" }}>{result.risk_band}</span> risk · {pct}% probability · {Math.round(result.confidence * 100)}% confidence
              </p>
            </div>
            <span className={`chip ${ui.chip}`}><span className="d" /> {result.algorithm}</span>
          </div>

          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="bar"><i style={{ width: `${pct}%`, background: ui.color }} /></div>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--ink-2)" }}>{result.verdict}</p>

            <div className="meaning">
              <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--muted-hex)" }}>What this means</p>
              <p style={{ marginTop: 4, fontSize: 13.5, color: "var(--ink-2)" }}>{result.risk_explanation}</p>
            </div>

            {result.factors.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--muted-hex)" }}>Why - top reasons (SHAP)</p>
                {result.factors.map((f, i) => {
                  const isFraud = f.signal === "fraud";
                  const c = isFraud ? "var(--crit)" : "var(--safe)";
                  return (
                    <div key={f.feature + i} style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12.5 }}>
                        <span style={{ fontWeight: 500, color: "var(--ink)" }}>{f.label}</span>
                        <span style={{ fontWeight: 600, color: c }}>{isFraud ? "↑ raises risk" : "↓ lowers risk"}</span>
                      </div>
                      <div className="bar" style={{ height: 6 }}>
                        <i style={{ width: `${(Math.abs(f.weight) / maxWeight) * 100}%`, background: c }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Automation: push the scored transaction into the live engine. */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap", borderTop: "1px solid var(--border-hex)", paddingTop: 14 }}>
              <p style={{ fontSize: 12, color: "var(--muted-hex)" }}>
                {ingest.isSuccess
                  ? <span style={{ color: "var(--safe)", fontWeight: 600 }}>✓ Streamed to the live engine.</span>
                  : "Feed this into automated monitoring - it updates the security score, heatmap and alerts in real time."}
              </p>
              {ingest.isSuccess ? (
                <Link href="/monitor" className="head-btn"><Radio /> View on live monitor</Link>
              ) : authed ? (
                <button className="head-btn" onClick={() => ingest.mutate()} disabled={ingest.isPending}>
                  {ingest.isPending ? <><Loader2 className="animate-spin" /> Sending…</> : <><Send /> Push to live monitor</>}
                </button>
              ) : (
                <Link href="/login" className="head-btn"><Send /> Log in to automate</Link>
              )}
            </div>
            {ingest.error && <p className="alert-error">Could not push to the engine. Are you signed in?</p>}

            <p style={{ fontSize: 11.5, color: "var(--muted-hex)" }}>{result.algorithm} · {result.model_version}</p>
          </div>
        </div>
      )}
    </div>
  );
}
