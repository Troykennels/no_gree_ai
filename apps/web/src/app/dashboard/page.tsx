"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { LogOut, ShieldAlert, ShieldCheck, ScanLine, Download } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, ApiError, tokenStore } from "@/lib/api";
import { riskTheme } from "@/lib/risk";
import { cn, downloadCsv, formatDate, formatPercent } from "@/lib/utils";
import { RiskDistributionChart } from "@/components/dashboard/risk-chart";

export default function DashboardPage() {
  const router = useRouter();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    retry: false,
  });

  const scansQuery = useQuery({
    queryKey: ["scans"],
    queryFn: () => api.scans(50, 0),
    enabled: meQuery.isSuccess,
  });

  useEffect(() => {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      router.replace("/login");
    }
  }, [meQuery.error, router]);

  const scans = scansQuery.data?.items ?? [];
  const total = scansQuery.data?.total ?? 0;
  const fraudCount = scans.filter((s) => s.assessment.is_fraud).length;
  const safeCount = scans.length - fraudCount;

  function logout() {
    tokenStore.clear();
    router.push("/");
  }

  function exportCsv() {
    downloadCsv(
      `securenaija-scans-${new Date().toISOString().slice(0, 10)}.csv`,
      scans.map((s) => ({
        date: s.created_at,
        channel: s.channel,
        message: s.message,
        fraud_probability: s.assessment.fraud_probability,
        is_fraud: s.assessment.is_fraud,
        risk_band: s.assessment.risk_band,
        risk_label: s.assessment.risk_label,
        verdict: s.assessment.verdict,
      })),
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-border/60 glass">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <Button size="sm" variant="outline" onClick={exportCsv} disabled={scans.length === 0}>
              <Download /> Download CSV
            </Button>
            <Link href="/detector">
              <Button size="sm">
                <ScanLine /> New scan
              </Button>
            </Link>
            <Button size="sm" variant="ghost" onClick={logout}>
              <LogOut /> Log out
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-10">
        <div className="mb-8">
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {meQuery.data
              ? `Welcome, ${meQuery.data.full_name.split(" ")[0]}`
              : "Your dashboard"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Every message you check is saved here, with its fraud verdict.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Total scans"
            value={total}
            icon={<ScanLine className="size-5 text-primary" />}
          />
          <StatCard
            label="Fraud caught"
            value={fraudCount}
            icon={<ShieldAlert className="size-5 text-danger" />}
            accent="text-danger"
          />
          <StatCard
            label="Marked safe"
            value={safeCount}
            icon={<ShieldCheck className="size-5 text-success" />}
            accent="text-success"
          />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <Card className="p-6">
            <h2 className="mb-4 font-semibold">Recent scans</h2>
            {scansQuery.isLoading ? (
              <SkeletonList />
            ) : scans.length === 0 ? (
              <EmptyState />
            ) : (
              <ul className="divide-y divide-border">
                {scans.map((s) => {
                  const theme = riskTheme(s.assessment.risk_band);
                  return (
                    <li key={s.id} className="flex items-start gap-3 py-3.5">
                      <span
                        className={cn(
                          "mt-1 size-2.5 shrink-0 rounded-full",
                          s.assessment.is_fraud ? "bg-danger" : "bg-success",
                        )}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm text-foreground/90">
                          {s.message}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {s.channel.toUpperCase()} · {formatDate(s.created_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={cn("text-sm font-bold", theme.text)}>
                          {formatPercent(s.assessment.fraud_probability)}
                        </span>
                        <Badge
                          variant={s.assessment.is_fraud ? "danger" : "success"}
                          className="ml-2"
                        >
                          {s.assessment.risk_label}
                        </Badge>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>

          <Card className="p-6">
            <h2 className="mb-4 font-semibold">Risk distribution</h2>
            <RiskDistributionChart scans={scans} />
          </Card>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  accent?: string;
}) {
  return (
    <Card className="flex items-center justify-between p-6">
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={cn("mt-1 text-3xl font-bold tabular-nums", accent)}>
          {value}
        </p>
      </div>
      <span className="grid size-11 place-items-center rounded-xl bg-secondary">
        {icon}
      </span>
    </Card>
  );
}

function SkeletonList() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <ScanLine className="size-8 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">
        No scans yet. Check your first suspicious message.
      </p>
      <Link href="/detector">
        <Button size="sm">Open the detector</Button>
      </Link>
    </div>
  );
}
