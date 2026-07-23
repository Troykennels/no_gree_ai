import type { ReactNode } from "react";

/** Page header rendered as the mockup's .page-head (title + description + actions). */
export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div style={{ minWidth: 0 }}>
        {eyebrow ? <p className="eyebrow-label">{eyebrow}</p> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div style={{ display: "flex", gap: 10, flexShrink: 0 }}>{actions}</div> : null}
    </div>
  );
}
