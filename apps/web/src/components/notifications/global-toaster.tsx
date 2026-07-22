"use client";

import { useLiveData } from "@/lib/live-provider";
import { Toaster } from "@/components/monitor/toaster";

/** Renders the app-wide toast stack from the live notification context. */
export function GlobalToaster() {
  const { toasts, dismissToast } = useLiveData();
  return <Toaster toasts={toasts} onDismiss={dismissToast} />;
}
