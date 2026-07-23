"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Database,
  FileWarning,
  Layers,
  Percent,
} from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { AdminGate } from "@/components/app/admin-gate";
import { PageHeader } from "@/components/app/page-header";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, formatPercent } from "@/lib/utils";
import type { DatasetReport, DatasetStats } from "@/lib/report-types";
import {
  CategoryChart,
  ClassDistributionChart,
  RatioPie,
} from "@/components/admin/dataset-charts";

const FRAUD = "hsl(0 84% 60%)";
const LEGIT = "hsl(158 84% 39%)";

async function fetchReport(): Promise<DatasetReport> {
  const res = await fetch("/reports/dataset_report.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Report not found. Run the preprocessing pipeline first.");
  return res.json();
}

export default function AdminDatasetsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dataset-report"],
    queryFn: fetchReport,
    retry: false,
  });

  return (
    <AppShell>
      <AdminGate>
      <PageHeader
        eyebrow="Admin"
        title="Dataset Intelligence"
        description="Size, class balance, missing values and fraud/scam ratios across every training dataset."
      />

      {isLoading && <SkeletonGrid />}

        {error && (
          <Card className="flex items-center gap-3 border-warning/40 p-6">
            <FileWarning className="size-5 text-warning" />
            <div>
              <p className="font-semibold">No report yet</p>
              <p className="text-sm text-muted-foreground">
                Run{" "}
                <code className="rounded bg-secondary px-1.5 py-0.5 text-xs">
                  python -m snaija_ml.data.preprocess
                </code>{" "}
                to generate the dataset report and charts.
              </p>
            </div>
          </Card>
        )}

        {data && (
          <>
            <OverviewRow report={data} />
            <div className="mt-8 grid gap-6">
              {Object.entries(data.datasets).map(([key, ds]) => (
                <DatasetCard key={key} ds={ds} />
              ))}
            </div>
            <ChartGallery charts={data.generated_charts} />
          </>
        )}
      </AdminGate>
    </AppShell>
  );
}

function OverviewRow({ report }: { report: DatasetReport }) {
  const tiles = [
    {
      label: "Datasets",
      value: report.summary?.total_datasets ?? Object.keys(report.datasets).length,
      icon: <Layers className="size-5 text-primary" />,
    },
    {
      label: "Total rows",
      value: (report.summary?.total_rows ?? 0).toLocaleString(),
      icon: <Database className="size-5 text-accent-foreground" />,
    },
    {
      label: "Fraud typologies",
      value: Object.keys(
        report.datasets.nigeria_fraud_sms?.category_distribution ?? {},
      ).filter((c) => !c.toLowerCase().startsWith("legit")).length,
      icon: <AlertTriangle className="size-5 text-danger" />,
    },
  ];
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {tiles.map((t) => (
        <Card key={t.label} className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm text-muted-foreground">{t.label}</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">{t.value}</p>
          </div>
          <span className="grid size-11 place-items-center rounded-xl bg-secondary">
            {t.icon}
          </span>
        </Card>
      ))}
    </div>
  );
}

function DatasetCard({ ds }: { ds: DatasetStats }) {
  if (ds.status === "not_downloaded" || ds.status === "error") {
    return (
      <Card className="border-warning/40 p-6">
        <div className="flex items-center gap-3">
          <FileWarning className="size-5 text-warning" />
          <div>
            <h2 className="font-semibold">{ds.name}</h2>
            <p className="text-xs text-muted-foreground">{ds.purpose}</p>
          </div>
          <Badge variant="warning" className="ml-auto">
            {ds.status === "error" ? "Unavailable" : "Not downloaded"}
          </Badge>
        </div>
        <p className="mt-4 rounded-lg bg-warning/10 px-3 py-2 text-xs text-warning">
          {ds.note}
        </p>
      </Card>
    );
  }

  const dist = ds.class_distribution ?? {};
  const posKey = Object.keys(dist).find((k) => k === "1") ?? "1";
  const negKey = Object.keys(dist).find((k) => k === "0") ?? "0";
  const isText = ds.kind === "text";
  const posName = isText ? (ds.name.includes("Spam") ? "Spam" : "Fraud") : "Fraud";
  const negName = isText ? (ds.name.includes("Spam") ? "Ham" : "Legit") : "Legit";

  const classData = [
    { name: posName, value: dist[posKey] ?? 0, fill: FRAUD },
    { name: negName, value: dist[negKey] ?? 0, fill: LEGIT },
  ];
  const ratio = ds.fraud_ratio ?? ds.scam_ratio ?? ds.positive_ratio ?? 0;

  const scamCats = Object.entries(ds.category_distribution ?? {})
    .filter(([k]) => !k.toLowerCase().startsWith("legit"))
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold">{ds.name}</h2>
        <Badge variant={ds.kind === "text" ? "primary" : "default"}>{ds.kind}</Badge>
        <span className="text-sm text-muted-foreground">{ds.purpose}</span>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Rows" value={(ds.rows_processed ?? 0).toLocaleString()} icon={<Database className="size-4" />} />
        <Stat
          label={ds.name.includes("Spam") ? "Scam ratio" : "Fraud ratio"}
          value={formatPercent(ratio, 1)}
          icon={<Percent className="size-4" />}
          accent="text-danger"
        />
        <Stat
          label="Missing values"
          value={(ds.missing_values ?? 0).toLocaleString()}
          icon={<FileWarning className="size-4" />}
        />
        <Stat
          label="Balance ratio"
          value={(ds.class_balance_ratio ?? 0).toFixed(2)}
          icon={<Layers className="size-4" />}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Class distribution
          </p>
          <ClassDistributionChart data={classData} />
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {ds.name.includes("Spam") ? "Spam" : "Fraud"} vs legitimate
          </p>
          <RatioPie data={classData} />
        </div>
      </div>

      {scamCats.length > 0 && (
        <div className="mt-6">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Scam categories
          </p>
          <CategoryChart data={scamCats} />
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-2 text-xs text-muted-foreground">
        {ds.duplicates_removed != null && (
          <Badge variant="outline">{ds.duplicates_removed} duplicates removed</Badge>
        )}
        {ds.outliers_removed != null && (
          <Badge variant="outline">{ds.outliers_removed} outliers removed</Badge>
        )}
        {ds.outliers_clipped != null && (
          <Badge variant="outline">{ds.outliers_clipped} outliers clipped</Badge>
        )}
        {ds.avg_token_count != null && (
          <Badge variant="outline">avg {ds.avg_token_count} tokens</Badge>
        )}
        {ds.n_features != null && (
          <Badge variant="outline">{ds.n_features} features</Badge>
        )}
      </div>
    </Card>
  );
}

function Stat({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className={cn("mt-1 text-xl font-bold tabular-nums", accent)}>{value}</p>
    </div>
  );
}

function ChartGallery({ charts }: { charts: string[] }) {
  if (!charts?.length) return null;
  return (
    <div className="mt-10">
      <h2 className="mb-4 font-display text-xl font-bold">Generated charts</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {charts.map((c) => (
          <Card key={c} className="overflow-hidden p-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`/reports/${c}`}
              alt={c}
              className="w-full rounded-lg"
              loading="lazy"
            />
          </Card>
        ))}
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-24 animate-pulse rounded-2xl bg-muted" />
      ))}
    </div>
  );
}
