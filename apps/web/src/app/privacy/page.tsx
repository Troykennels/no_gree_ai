"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Download, ShieldCheck, Eye, FileLock2, Trash2, Server } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useMe } from "@/lib/use-me";
import { downloadCsv } from "@/lib/utils";

const STORED = [
  { icon: Eye, title: "What we store", body: "Your account (name, email), and the messages you choose to save, with their fraud verdict." },
  { icon: FileLock2, title: "PII is redacted", body: "BVN, NIN, card numbers, OTP and PINs are masked before anything is stored or shown." },
  { icon: Server, title: "Where it lives", body: "An encrypted-at-rest database. We never sell your data or share it with third parties." },
  { icon: ShieldCheck, title: "Your rights (NDPR)", body: "Access, download and delete your data at any time. You control it." },
];

export default function PrivacyPage() {
  const me = useMe();
  const scans = useQuery({
    queryKey: ["scans", "all"],
    queryFn: () => api.scans(200, 0),
    enabled: me.isSuccess,
  });

  function exportData() {
    const items = scans.data?.items ?? [];
    downloadCsv(
      `nogree-my-data-${new Date().toISOString().slice(0, 10)}.csv`,
      items.map((s) => ({
        date: s.created_at, channel: s.channel, message: s.message,
        fraud_probability: s.assessment.fraud_probability, risk_band: s.assessment.risk_band,
        verdict: s.assessment.verdict,
      })),
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <PageHeader
          eyebrow="Trust & compliance"
          title="Privacy Centre"
          description="No Gree AI is built for Nigeria and aligned with the NDPR. Here is exactly what we collect, how we protect it, and how you stay in control."
        />

        <div className="grid gap-4 sm:grid-cols-2">
          {STORED.map(({ icon: Icon, title, body }) => (
            <Card key={title} className="p-6">
              <span className="grid size-10 place-items-center rounded-xl bg-primary/10">
                <Icon className="size-5 text-primary" />
              </span>
              <h2 className="mt-4 font-semibold">{title}</h2>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{body}</p>
            </Card>
          ))}
        </div>

        <Card className="mt-4 flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-semibold">Download my data</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Export everything we hold about you as a CSV file.
            </p>
          </div>
          <Button variant="outline" onClick={exportData}
            disabled={!me.isSuccess || (scans.data?.items.length ?? 0) === 0}>
            <Download /> Download CSV
          </Button>
        </Card>

        <Card className="mt-4 flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="flex items-center gap-2 font-semibold">
              <Trash2 className="size-4 text-danger" /> Delete my data
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Permanently remove your account and all saved scans. This cannot be undone.
            </p>
          </div>
          <Link href="/settings">
            <Button variant="outline" className="border-danger/40 text-danger hover:bg-danger/10">
              Manage in Settings
            </Button>
          </Link>
        </Card>

        {!me.isSuccess && !me.isLoading ? (
          <p className="mt-6 text-center text-sm text-muted-foreground">
            <Link href="/login" className="font-semibold text-primary hover:underline">Log in</Link>{" "}
            to download or delete your personal data.
          </p>
        ) : null}
      </div>
    </AppShell>
  );
}
