"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  User, Bell, ShieldCheck, Trash2, BadgeCheck, Loader2, Check,
} from "lucide-react";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, tokenStore } from "@/lib/api";
import { useMe } from "@/lib/use-me";
import { useLiveData } from "@/lib/live-provider";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  const router = useRouter();
  const me = useMe();
  const { permission, requestBrowserPermission } = useLiveData();
  const [deleting, setDeleting] = useState(false);
  const [confirm, setConfirm] = useState(false);

  const user = me.data;

  async function deleteAccount() {
    setDeleting(true);
    try {
      await api.deleteAccount();
      tokenStore.clear();
      router.push("/");
    } catch {
      setDeleting(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl">
        <PageHeader
          eyebrow="Account"
          title="Settings"
          description="Manage your profile, notifications, security and data."
        />

        {me.isLoading ? (
          <div className="space-y-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-28 animate-pulse rounded-2xl bg-muted/50" />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Profile */}
            <Card className="p-6">
              <SectionTitle icon={<User className="size-4 text-primary" />} title="Profile" />
              <div className="mt-4 flex items-center gap-4">
                <div className="grid size-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-primary to-emerald-400 text-lg font-bold text-primary-foreground">
                  {(user?.full_name ?? "?").slice(0, 1).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-semibold">
                    {user?.full_name}
                    {user?.role === "admin" ? (
                      <Badge variant="outline"><BadgeCheck className="size-3" /> Admin</Badge>
                    ) : null}
                  </p>
                  <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Member since {formatDate(user?.created_at) || "today"}
                  </p>
                </div>
              </div>
            </Card>

            {/* Notifications */}
            <Card className="p-6">
              <SectionTitle icon={<Bell className="size-4 text-primary" />} title="Notifications" />
              <p className="mt-2 text-sm text-muted-foreground">
                Get desktop alerts for high-risk fraud, even when No Gree AI is in a
                background tab.
              </p>
              <div className="mt-4">
                {permission === "granted" ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-medium text-success">
                    <Check className="size-4" /> Desktop alerts enabled
                  </span>
                ) : permission === "unsupported" ? (
                  <span className="text-sm text-muted-foreground">
                    Your browser does not support desktop notifications.
                  </span>
                ) : (
                  <Button size="sm" variant="outline" onClick={requestBrowserPermission}>
                    <Bell /> Enable desktop alerts
                  </Button>
                )}
              </div>
            </Card>

            {/* Security */}
            <Card className="p-6">
              <SectionTitle icon={<ShieldCheck className="size-4 text-primary" />} title="Security" />
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2"><Check className="size-4 text-success" /> Password stored with bcrypt (never in plain text)</li>
                <li className="flex items-center gap-2"><Check className="size-4 text-success" /> Sessions use short-lived signed tokens</li>
                <li className="flex items-center gap-2"><Check className="size-4 text-success" /> Your scanned messages are PII-redacted before storage</li>
              </ul>
            </Card>

            {/* Danger zone */}
            <Card className="border-danger/25 bg-danger/[0.03] p-6">
              <SectionTitle icon={<Trash2 className="size-4 text-danger" />} title="Delete account" />
              <p className="mt-2 text-sm text-muted-foreground">
                Permanently delete your account and all saved scan history. This cannot be
                undone.
              </p>
              {confirm ? (
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <Button size="sm" variant="ghost" onClick={() => setConfirm(false)} disabled={deleting}>
                    Cancel
                  </Button>
                  <Button size="sm" variant="danger" onClick={deleteAccount} disabled={deleting}>
                    {deleting ? <Loader2 className="animate-spin" /> : <Trash2 />}
                    Yes, delete everything
                  </Button>
                </div>
              ) : (
                <Button size="sm" variant="outline" className="mt-4 border-danger/40 text-danger hover:bg-danger/10"
                  onClick={() => setConfirm(true)}>
                  <Trash2 /> Delete my account
                </Button>
              )}
            </Card>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <h2 className="font-semibold">{title}</h2>
    </div>
  );
}
