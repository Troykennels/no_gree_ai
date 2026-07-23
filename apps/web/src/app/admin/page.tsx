"use client";

import Link from "next/link";
import { Database, ScrollText, LayoutDashboard, ShieldCheck, Users, Activity } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { AdminGate } from "@/components/app/admin-gate";
import { Card } from "@/components/ui/card";
import { useLiveData } from "@/lib/live-provider";

const TOOLS = [
  { href: "/admin/datasets", icon: Database, title: "Dataset intelligence", desc: "Data quality, class balance and preprocessing report for every training corpus." },
  { href: "/admin/audit-logs", icon: ScrollText, title: "Audit logs", desc: "Security trail: sign-in failures, admin access and account changes." },
  { href: "/monitor", icon: LayoutDashboard, title: "Live command center", desc: "Real-time fraud dashboard, timeline, heatmap and alerts." },
];

export default function AdminPage() {
  const { state } = useLiveData();
  const s = state?.stats;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Admin"
        title="Admin Dashboard"
        description="Platform operations, data intelligence and the security audit trail."
      />
      <AdminGate>
            <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat icon={ShieldCheck} label="Security score" value={state ? `${Math.round(state.security_score)}` : "-"} suffix="/100" />
              <Stat icon={Activity} label="Messages scanned" value={s ? s.messages_scanned.toLocaleString() : "-"} />
              <Stat icon={Users} label="Transactions" value={s ? s.transactions_analyzed.toLocaleString() : "-"} />
              <Stat icon={ScrollText} label="Alerts raised" value={s ? s.alerts.toLocaleString() : "-"} />
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {TOOLS.map((t) => (
                <Link key={t.href} href={t.href}>
                  <Card className="group h-full p-6 transition-colors hover:border-primary/40">
                    <span className="grid size-10 place-items-center rounded-xl bg-primary/10">
                      <t.icon className="size-5 text-primary" />
                    </span>
                    <h2 className="mt-4 font-semibold group-hover:text-primary">{t.title}</h2>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{t.desc}</p>
                  </Card>
                </Link>
              ))}
            </div>
      </AdminGate>
    </AppShell>
  );
}

function Stat({ icon: Icon, label, value, suffix }: {
  icon: typeof ShieldCheck; label: string; value: string; suffix?: string;
}) {
  return (
    <Card className="flex items-center justify-between p-5">
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-bold tabular-nums">
          {value}{suffix ? <span className="text-sm text-muted-foreground">{suffix}</span> : null}
        </p>
      </div>
      <span className="grid size-10 place-items-center rounded-xl bg-secondary">
        <Icon className="size-5 text-primary" />
      </span>
    </Card>
  );
}
