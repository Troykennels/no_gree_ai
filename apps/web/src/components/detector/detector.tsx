"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2, Scan, Sparkles, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Channel, RiskBand, Scan as ScanType } from "@/lib/types";

const SAMPLES: { label: string; channel: Channel; text: string }[] = [
  {
    label: "Fake bank alert",
    channel: "sms",
    text: "Dear Customer, your GTBank account will be BLOCKED today. Update your BVN now via http://gtb-verify.top/login to avoid deactivation.",
  },
  {
    label: "Loan scam",
    channel: "whatsapp",
    text: "CONGRATULATIONS! You are pre-approved for an instant loan of N150,000, NO collateral. Pay a small processing fee to unlock. Apply: bit.ly/loan-ng",
  },
  {
    label: "Real credit alert",
    channel: "sms",
    text: "Access Bank: Credit Alert. Acct **4821. Amt:NGN25,000. Desc:Transfer from Chidi. Bal:NGN61,300.",
  },
];

const CHANNELS: { value: Channel; label: string }[] = [
  { value: "sms", label: "SMS" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "pos", label: "POS alert" },
  { value: "email", label: "Email" },
  { value: "other", label: "Other" },
];

const BAND_COLOR: Record<RiskBand, string> = {
  critical: "var(--crit)",
  high: "var(--high)",
  elevated: "var(--med)",
  low: "var(--low)",
  minimal: "var(--safe)",
};
const BAND_TINT: Record<RiskBand, string> = {
  critical: "var(--crit-t)",
  high: "var(--high-t)",
  elevated: "var(--med-t)",
  low: "var(--low-t)",
  minimal: "var(--safe-t)",
};

export function Detector({ compact = false, initialMessage = "" }: { compact?: boolean; initialMessage?: string }) {
  const [message, setMessage] = useState(initialMessage);
  const [channel, setChannel] = useState<Channel>("sms");

  useEffect(() => {
    if (initialMessage) setMessage(initialMessage);
  }, [initialMessage]);

  const mutation = useMutation<ScanType, Error, void>({
    mutationFn: () => api.detect(message.trim(), channel),
  });

  const errorText =
    mutation.error instanceof ApiError
      ? mutation.error.status === 503
        ? "The fraud model is still starting up. Please try again in a moment."
        : mutation.error.message
      : mutation.error
        ? "Could not reach the No Gree AI API. Is it running?"
        : null;

  const a = mutation.data?.assessment;
  const color = a ? BAND_COLOR[a.risk_band] : "var(--safe)";
  const tint = a ? BAND_TINT[a.risk_band] : "var(--safe-t)";
  const pct = a ? Math.round(a.fraud_probability * 100) : 0;
  const Icon = a?.is_fraud ? ShieldAlert : ShieldCheck;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="card pad">
        <div style={{ marginBottom: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {CHANNELS.map((c) => (
            <button
              key={c.value}
              onClick={() => setChannel(c.value)}
              aria-pressed={channel === c.value}
              className="sample"
              style={
                channel === c.value
                  ? { background: "var(--brand-tint)", color: "var(--brand-700)", borderColor: "var(--brand-tint)" }
                  : undefined
              }
            >
              {c.label}
            </button>
          ))}
        </div>

        <textarea
          aria-label="Message to scan for fraud"
          className="ng-textarea"
          style={compact ? { minHeight: 104 } : undefined}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Paste the suspicious SMS, WhatsApp message, POS alert or loan offer here…"
          maxLength={5000}
        />

        <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "var(--muted-hex)" }}>Try:</span>
            {SAMPLES.map((sm) => (
              <button key={sm.label} className="sample" onClick={() => { setMessage(sm.text); setChannel(sm.channel); mutation.reset(); }}>
                {sm.label}
              </button>
            ))}
          </div>

          <button className="head-btn primary" onClick={() => mutation.mutate()} disabled={!message.trim() || mutation.isPending}>
            {mutation.isPending ? <><Loader2 className="animate-spin" /> Analysing…</> : <><Scan /> Analyse message</>}
          </button>
        </div>

        {errorText && <p className="alert-error">{errorText}</p>}
      </div>

      {a ? (
        <div className="card reveal in">
          <div className="result-head">
            <span className="ric" style={{ background: tint, color }}>
              <Icon />
            </span>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: 700, color, fontSize: 15 }}>{a.risk_label}</p>
              <p style={{ fontSize: 12, color: "var(--muted-hex)" }}>{pct}% fraud probability</p>
            </div>
            <span className="chip" style={{ background: tint, color }}>
              <span className="d" style={{ background: color }} /> {a.risk_band}
            </span>
          </div>
          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="bar"><i style={{ width: `${pct}%`, background: color }} /></div>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--ink-2)" }}>{a.verdict}</p>
            {a.factors.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--muted-hex)" }}>Signals</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {a.factors.map((f, i) => (
                    <span
                      key={f.label + i}
                      className="chip"
                      style={
                        f.signal === "fraud"
                          ? { background: "var(--crit-t)", color: "var(--crit)" }
                          : { background: "var(--safe-t)", color: "var(--safe)" }
                      }
                    >
                      <span className="d" style={{ background: f.signal === "fraud" ? "var(--crit)" : "var(--safe)" }} />
                      {f.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <p style={{ fontSize: 11.5, color: "var(--muted-hex)" }}>Model {a.model_version}</p>
          </div>
        </div>
      ) : (
        !compact && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, borderRadius: 16, border: "1px dashed var(--border-2)", padding: "40px 20px", fontSize: 13, color: "var(--muted-hex)" }}>
            <Sparkles style={{ width: 16, height: 16, color: "var(--brand)" }} />
            Your fraud analysis and explanation will appear here.
          </div>
        )
      )}
    </div>
  );
}
