"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2, ShieldCheck, ShieldAlert, AlertTriangle, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ScamLabel, ScamResult } from "@/lib/types";
import { useState } from "react";

const SAMPLES: { label: string; text: string }[] = [
  {
    label: "Fake bank alert",
    text: "Dear Customer, your GTBank account will be BLOCKED today. Update your BVN now via http://gtb-verify.top/login to avoid deactivation.",
  },
  {
    label: "Loan scam",
    text: "CONGRATULATIONS! You are pre-approved for an instant loan of N150,000, NO collateral. Pay a small processing fee to unlock. Apply: bit.ly/loan-ng",
  },
  {
    label: "Real credit alert",
    text: "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Desc:Transfer from Chidi. Bal:NGN61,300.",
  },
];

const UI: Record<ScamLabel, { icon: typeof ShieldCheck; color: string; tint: string; chip: string }> = {
  Scam: { icon: AlertTriangle, color: "var(--crit)", tint: "var(--crit-t)", chip: "c-crit" },
  Suspicious: { icon: ShieldAlert, color: "var(--med)", tint: "var(--med-t)", chip: "c-med" },
  Safe: { icon: ShieldCheck, color: "var(--safe)", tint: "var(--safe-t)", chip: "c-safe" },
};

export function ScamAnalyzer() {
  const [message, setMessage] = useState("");

  const mutation = useMutation<ScamResult, Error, void>({
    mutationFn: () => api.detectScam(message.trim()),
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The scam-detection model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the No_Gree AI API. Is it running?"
        : null;

  const result = mutation.data;
  const ui = result ? UI[result.label] : UI.Safe;
  const Icon = ui.icon;
  const pct = result ? Math.round(result.scam_probability * 100) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="card pad">
        <textarea
          aria-label="Message to check for a scam"
          className="ng-textarea"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste the suspicious SMS, WhatsApp message or email here…"
          maxLength={5000}
        />

        <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "var(--muted-hex)" }}>Try:</span>
            {SAMPLES.map((sm) => (
              <button key={sm.label} className="sample" onClick={() => { setMessage(sm.text); mutation.reset(); }}>
                {sm.label}
              </button>
            ))}
          </div>

          <button className="head-btn primary" onClick={() => mutation.mutate()} disabled={!message.trim() || mutation.isPending}>
            {mutation.isPending ? <><Loader2 className="animate-spin" /> Analysing…</> : <><Sparkles /> Check for scam</>}
          </button>
        </div>

        {errorText && <p className="alert-error">{errorText}</p>}
      </div>

      {result ? (
        <div className="card reveal in">
          <div className="result-head">
            <span className="ric" style={{ background: ui.tint, color: ui.color }}>
              <Icon />
            </span>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 700, color: ui.color, fontSize: 15 }}>{result.label}</p>
              <p style={{ fontSize: 12, color: "var(--muted-hex)" }}>Confidence {Math.round(result.confidence * 100)}%</p>
            </div>
            <span className={`chip ${ui.chip}`}><span className="d" /> {pct}% scam</span>
          </div>

          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="bar">
              <i style={{ width: `${pct}%`, background: ui.color }} />
            </div>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--ink-2)" }}>{result.explanation}</p>

            {result.highlighted_words.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--muted-hex)" }}>
                  Suspicious words
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {result.highlighted_words.map((w, i) => (
                    <span key={w.word + i} className="chip-word">{w.word}</span>
                  ))}
                </div>
              </div>
            )}

            <p style={{ fontSize: 11.5, color: "var(--muted-hex)" }}>Model {result.model_version}</p>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 16, border: "1px dashed var(--border-2)", padding: "40px 20px", fontSize: 13, color: "var(--muted-hex)" }}>
          <Sparkles style={{ width: 16, height: 16, color: "var(--brand)" }} />
          Your Safe / Suspicious / Scam verdict will appear here.
        </div>
      )}
    </div>
  );
}
