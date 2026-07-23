import { BrainCircuit, Lock, ShieldCheck } from "lucide-react";

const TRUST = [
  {
    icon: Lock,
    title: "Bank-grade security",
    body: "Your data is encrypted in transit and at rest.",
  },
  {
    icon: ShieldCheck,
    title: "NDPR compliant",
    body: "Built to Nigeria's data-protection standards.",
  },
  {
    icon: BrainCircuit,
    title: "AI fraud intelligence",
    body: "Two ML models fused into one 0–100 risk score.",
  },
];

/** The cinematic, always-dark brand column shown beside the auth forms. */
export function AuthBrandPanel() {
  return (
    <div className="brand-panel">
      <div className="inner">
        <span className="logo-badge" style={{ width: 168, height: 168, borderRadius: 40 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.jpg" alt="No_Gree AI" />
        </span>
        <h1>No_Gree AI</h1>
        <p className="tagline">
          <span style={{ color: "var(--neon-green)" }}>Detect.</span>
          <span className="s">·</span>
          <span>Protect.</span>
          <span className="s">·</span>
          <span style={{ color: "var(--neon-red)" }}>Prevent.</span>
        </p>
        <p className="subtag">Intelligent fraud detection &amp; risk intelligence</p>

        <div className="trust">
          {TRUST.map((t) => {
            const Icon = t.icon;
            return (
              <div className="t" key={t.title}>
                <span className="ic">
                  <Icon />
                </span>
                <div>
                  <b>{t.title}</b>
                  <p>{t.body}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="poweredby">
        Powered by <b>No_Gree AI</b>
      </p>
    </div>
  );
}
