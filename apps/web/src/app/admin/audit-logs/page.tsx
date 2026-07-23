"use client";

import { useQuery } from "@tanstack/react-query";
import { ScrollText, Download, AlertTriangle, ShieldCheck, UserX, Ban } from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { AdminGate } from "@/components/app/admin-gate";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useMe } from "@/lib/use-me";
import { cn, downloadCsv, formatDate } from "@/lib/utils";

const EVENT_UI: Record<string, { icon: typeof ShieldCheck; cls: string }> = {
  admin_access: { icon: ShieldCheck, cls: "text-success" },
  rbac_denied: { icon: Ban, cls: "text-warning" },
  InvalidCredentials: { icon: UserX, cls: "text-danger" },
  InactiveUser: { icon: UserX, cls: "text-warning" },
  account_deleted: { icon: AlertTriangle, cls: "text-danger" },
};

export default function AuditLogsPage() {
  const me = useMe();
  const logs = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => api.auditLogs(200),
    enabled: me.data?.role === "admin",
    refetchInterval: 15_000,
  });
  const items = logs.data?.items ?? [];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Admin"
        title="Audit Logs"
        description="A live security trail of authentication failures, admin access and account changes."
        actions={
          <Button variant="outline" size="sm" disabled={items.length === 0}
            onClick={() => downloadCsv(`nogree-audit-${new Date().toISOString().slice(0, 10)}.csv`, items)}>
            <Download /> Export
          </Button>
        }
      />
      <AdminGate>
            <Card className="overflow-hidden p-0">
              {logs.isLoading ? (
                <div className="space-y-px">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-14 animate-pulse bg-muted/40" />
                  ))}
                </div>
              ) : items.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-16 text-center">
                  <ScrollText className="size-7 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    No security events recorded yet. Failed logins and admin access will appear here.
                  </p>
                </div>
              ) : (
                <ul className="divide-y divide-border/60">
                  {items.map((e, i) => {
                    const ui = EVENT_UI[e.event] ?? { icon: ScrollText, cls: "text-muted-foreground" };
                    const Icon = ui.icon;
                    return (
                      <li key={`${e.ts}-${i}`} className="flex items-center gap-3 px-4 py-3">
                        <Icon className={cn("size-4 shrink-0", ui.cls)} />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-foreground/90">
                            {e.event.replace(/_/g, " ")}
                          </p>
                          <p className="truncate text-xs text-muted-foreground">
                            {e.actor}{e.detail ? ` · ${e.detail}` : ""}
                          </p>
                        </div>
                        <span className="shrink-0 text-xs text-muted-foreground">
                          {formatDate(e.ts)}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </Card>
      </AdminGate>
    </AppShell>
  );
}
