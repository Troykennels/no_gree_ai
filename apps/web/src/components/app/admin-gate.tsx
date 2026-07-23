"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Lock } from "lucide-react";
import { useMe } from "@/lib/use-me";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/** Client-side admin gate (the API enforces the real 403; this is UX). */
export function AdminGate({ children }: { children: ReactNode }) {
  const me = useMe();

  if (me.isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-muted/50" />
        ))}
      </div>
    );
  }

  if (me.data?.role !== "admin") {
    return (
      <Card className="mx-auto flex max-w-md flex-col items-center gap-3 p-10 text-center">
        <span className="grid size-12 place-items-center rounded-2xl bg-danger/10">
          <Lock className="size-6 text-danger" />
        </span>
        <h2 className="font-semibold">Admin access required</h2>
        <p className="text-sm text-muted-foreground">
          {me.isSuccess
            ? "Your account does not have the admin role. Contact your administrator."
            : "Please log in with an admin account to view this page."}
        </p>
        {!me.isSuccess ? (
          <Link href="/login"><Button size="sm">Log in</Button></Link>
        ) : null}
      </Card>
    );
  }

  return <>{children}</>;
}
