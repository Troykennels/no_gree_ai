"use client";

import { useMutation } from "@tanstack/react-query";
import {
  Loader2, Brain, Sparkles, AlertTriangle, ShieldAlert, AlertCircle,
  Info, ShieldCheck, CreditCard, MessageSquare, ChevronDown,
} from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { IntelligenceResult, Priority, RiskCategory } from "@/lib/types";

const CAT_COLOR: Record<RiskCategory, { color: string; tint: string }> = {
  Safe: { color: "var(--safe)", tint: "var(--safe-t)" },
  Low: { color: "var(--low)", tint: "var(--low-t)" },
  Medium: { color: "var(--med)", tint: "var(--med-t)" },
  High: { color: "var(--high)", tint: "var(--high-t)" },
  Critical: { color: "var(--crit)", tint: "var(--crit-t)" },
};

const PRIO: Record<Priority, { icon: typeof AlertTriangle; color: string; tint: string }> = {
  critical: { icon: AlertTriangle, color: "var(--crit)", tint: "var(--crit-t)" },
  high: { icon: ShieldAlert, color: "var(--high)", tint: "var(--high-t)" },
  medium: { icon: AlertCircle, color: "var(--med)", tint: "var(--med-t)" },
  low: { icon: Info, color: "var(--ink-2)", tint: "var(--surface-2)" },
  info: { icon: ShieldCheck, color: "var(--safe)", tint: "var(--safe-t)" },
};

const SAMPLE =
  "Your card **2290 was used for NGN180,000 abroad. If this wasn't you, call 08012345678 and confirm your OTP now to reverse it.";

function ScoreRing({ score, color }: { score: number; color: string }) {
  const R = 68, C = 2 * Math.PI * R;
  const dash = (Math.max(0, Math.min(100, score)) / 100) * C;
  return (
    <div className="gauge-wrap" style={{ width: 160, height: 160 }}>
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle className="track" cx="80" cy="80" r={R} fill="none" strokeWidth="13" />
        <circle cx="80" cy="80" r={R} fill="none" stroke={color} strokeWidth="13" strokeLinecap="round"
          strokeDasharray={`${dash} ${C - dash}`} style={{ transition: "stroke-dasharray .6s ease" }} />
      </svg>
      <div className="gauge-center">
        <span className="g-num" style={{ fontSize: 40 }}>{score}</span>
        <span className="g-of">/ 100</span>
      </div>
    </div>
  );
}

export function IntelligenceConsole() {
  const [message, setMessage] = useState("");
  const [showTxn, setShowTxn] = useState(false);
  const [amount, setAmount] = useState("");
  const [product, setProduct] = useState("C");
  const [cardType, setCardType] = useState("credit");
  const [email, setEmail] = useState("");

  const mutation = useMutation<IntelligenceResult, Error, void>({
    mutationFn: () => {
      const txn =
        showTxn && (amount || email)
          ? { TransactionAmt: amount ? Number(amount) : null, ProductCD: product, card6: cardType, P_emaildomain: email || null }
          : null;
      return api.assessIntelligence(message.trim() || null, txn);
    },
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 400
        ? "Enter a message or add a transaction to assess."
        : mutation.error.status === 503
          ? "The models are still starting up. Try again in a moment."
          : mutation.error.message
      : mutation.error
        ? "Could not reach the No_Gree AI API. Is it running?"
        : null;

  const canSubmit = message.trim().length > 0 || (showTxn && (amount || email));
  const result = mutation.data;
  const cat = result ? CAT_COLOR[result.category] : CAT_COLOR.Safe;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Input */}
      <div className="card pad">
        <textarea
          aria-label="Message to assess for fraud"
          className="ng-textarea"
          style={{ minHeight: 120 }}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste a suspicious message (optional if you add a transaction)…"
          maxLength={5000}
        />

        <button
          onClick={() => setShowTxn((v) => !v)}
          className="link-green"
          style={{ marginTop: 12, display: "inline-flex", alignItems: "center", gap: 6, background: "none", border: 0 }}
        >
          <CreditCard style={{ width: 15, height: 15 }} />
          {showTxn ? "Remove transaction" : "Add a transaction to combine"}
          <ChevronDown style={{ width: 15, height: 15, transform: showTxn ? "rotate(180deg)" : "none", transition: "transform .2s" }} />
        </button>

        {showTxn && (
          <div className="grid" style={{ gridTemplateColumns: "repeat(2, 1fr)", marginTop: 12 }}>
            <div>
              <label className="field-label" htmlFor="amt">Amount (₦)</label>
              <input id="amt" className="ng-input" type="number" placeholder="e.g. 180000" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </div>
            <div>
              <label className="field-label" htmlFor="iemail">Purchaser email domain</label>
              <input id="iemail" className="ng-input" placeholder="e.g. gmail.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="field-label" htmlFor="prod">Product category</label>
              <select id="prod" className="ng-select" value={product} onChange={(e) => setProduct(e.target.value)}>
                {["W", "C", "R", "H", "S"].map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="ictype">Card type</label>
              <select id="ictype" className="ng-select" value={cardType} onChange={(e) => setCardType(e.target.value)}>
                {["debit", "credit"].map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        )}

        <div style={{ marginTop: 16, display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <button className="sample" onClick={() => { setMessage(SAMPLE); mutation.reset(); }}>Try an example</button>
          <button className="head-btn primary" onClick={() => mutation.mutate()} disabled={!canSubmit || mutation.isPending}>
            {mutation.isPending ? <><Loader2 className="animate-spin" /> Assessing…</> : <><Brain /> Assess fraud risk</>}
          </button>
        </div>

        {errorText && <p className="alert-error">{errorText}</p>}
      </div>

      {/* Result */}
      {result ? (
        <div className="reveal in" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Overall */}
          <div className="card">
            <div className="result-head">
              <span className="ric" style={{ background: cat.tint, color: cat.color }}><Sparkles /></span>
              <div style={{ flex: 1 }}>
                <p style={{ fontWeight: 700, color: cat.color, fontSize: 15 }}>{result.category} risk</p>
                <p style={{ fontSize: 12, color: "var(--muted-hex)" }}>
                  Risk score {result.overall_risk_score}/100 · Confidence {Math.round(result.confidence * 100)}%
                </p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {result.scam && <span className="chip" style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}><MessageSquare style={{ width: 12, height: 12 }} /> {result.scam.label}</span>}
                {result.transaction && <span className="chip" style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}><CreditCard style={{ width: 12, height: 12 }} /> {result.transaction.decision}</span>}
              </div>
            </div>
            <div style={{ padding: 20, display: "grid", gridTemplateColumns: "auto 1fr", gap: 24, alignItems: "center" }}>
              <ScoreRing score={result.overall_risk_score} color={cat.color} />
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--ink-2)" }}>{result.human_explanation}</p>
                {result.signals.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {result.signals.map((s, i) => {
                      const p = PRIO[s.severity];
                      return <span key={`${s.type}-${i}`} className="chip" style={{ background: p.tint, color: p.color }}><span className="d" style={{ background: p.color }} /> {s.label}</span>;
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Reasons + meaning */}
          <div className="grid" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
            <div className="card pad">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <AlertTriangle style={{ width: 16, height: 16, color: "var(--brand-600)" }} />
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>Why - reasons</h3>
              </div>
              {result.reasons.length > 0 ? (
                <ul style={{ display: "flex", flexDirection: "column", gap: 8, listStyle: "none" }}>
                  {result.reasons.map((r, i) => (
                    <li key={r + i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13.5, color: "var(--ink-2)" }}>
                      <span style={{ width: 6, height: 6, borderRadius: "50%", background: cat.color, flex: "none" }} /> {r}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ fontSize: 13.5, color: "var(--muted-hex)" }}>No specific red flags - nothing stood out as fraudulent.</p>
              )}
            </div>
            <div className="card pad" style={{ borderColor: cat.color }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <ShieldAlert style={{ width: 16, height: 16, color: cat.color }} />
                <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>What this means</h3>
              </div>
              <p style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--ink-2)" }}>{result.risk_explanation}</p>
            </div>
          </div>

          {/* Recommendations */}
          <div className="card">
            <div className="card-h">
              <h3><Brain style={{ width: 16, height: 16, verticalAlign: "-3px", marginRight: 6, color: "var(--brand-600)" }} /> AI recommendations</h3>
              <span className="chip" style={{ background: "var(--brand-tint)", color: "var(--brand-700)" }}>{result.recommendations.length} actions</span>
            </div>
            {result.recommendations.map((r, i) => {
              const ui = PRIO[r.priority];
              const Icon = ui.icon;
              return (
                <div className="rec-item" key={r.id}>
                  <span className="rnum" style={{ background: ui.tint, color: ui.color }}>{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Icon style={{ width: 15, height: 15, color: ui.color, flex: "none" }} />
                      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--ink)" }}>{r.action}</p>
                      <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: ui.color }}>{r.priority}</span>
                    </div>
                    <p style={{ marginTop: 3, fontSize: 12.5, color: "var(--muted-hex)" }}>{r.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 16, border: "1px dashed var(--border-2)", padding: "40px 20px", fontSize: 13, color: "var(--muted-hex)" }}>
          <Sparkles style={{ width: 16, height: 16, color: "var(--brand)" }} />
          One fused 0-100 score, a risk category, and instant actions will appear here.
        </div>
      )}
    </div>
  );
}
