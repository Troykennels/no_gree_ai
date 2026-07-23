import { Check } from "lucide-react";

/** Two-card "How it works" (numbered pipeline) + "Advantages" (checklist) block. */
export function HowItWorks({
  steps,
  advantages,
  howTitle = "How it works",
  advTitle = "Advantages",
}: {
  steps: string[];
  advantages: string[];
  howTitle?: string;
  advTitle?: string;
}) {
  return (
    <div className="grid cols-12" style={{ marginTop: 20 }}>
      <div className="span-6">
        <div className="card" style={{ height: "100%" }}>
          <div className="card-h"><h3>{howTitle}</h3></div>
          <div style={{ padding: "8px 20px 18px" }}>
            {steps.map((s, i) => (
              <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0" }}>
                <span className="rnum" style={{ width: 24, height: 24 }}>{i + 1}</span>
                <p style={{ fontSize: 13.5, color: "var(--ink-2)", lineHeight: 1.55 }}>{s}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="span-6">
        <div className="card" style={{ height: "100%" }}>
          <div className="card-h"><h3>{advTitle}</h3></div>
          <div style={{ padding: "8px 20px 18px", display: "flex", flexDirection: "column", gap: 10 }}>
            {advantages.map((a, i) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                <span style={{ width: 20, height: 20, borderRadius: 6, flex: "none", display: "grid", placeItems: "center", background: "var(--safe-t)", color: "var(--safe)" }}>
                  <Check style={{ width: 13, height: 13 }} />
                </span>
                <p style={{ fontSize: 13.5, color: "var(--ink-2)", lineHeight: 1.5 }}>{a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
