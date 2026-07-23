"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bell, BellRing, Check, Trash2, X } from "lucide-react";
import { useLiveData } from "@/lib/live-provider";
import type { NotificationPriority } from "@/lib/types";
import { PRIORITY_STYLE } from "@/components/monitor/toaster";
import { cn } from "@/lib/utils";

const FILTERS: (NotificationPriority | "all")[] = ["all", "critical", "danger", "warning", "info"];

function ago(ts: number): string {
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function NotificationMenu() {
  const {
    notifications, unreadCount, permission,
    requestBrowserPermission, markAllRead, clearAll,
  } = useLiveData();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<NotificationPriority | "all">("all");
  const panelRef = useRef<HTMLDivElement>(null);

  // Accessibility: close on Escape and move focus into the panel when it opens.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    panelRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const shown = filter === "all" ? notifications : notifications.filter((n) => n.priority === filter);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="icon-btn"
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ""}`}
        aria-expanded={open}
      >
        {unreadCount > 0 ? <BellRing /> : <Bell />}
        {unreadCount > 0 && <span className="badge">{unreadCount > 9 ? "9+" : unreadCount}</span>}
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden />
            <motion.div
              ref={panelRef}
              tabIndex={-1}
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.16 }}
              className="absolute right-0 z-50 mt-2 w-[min(92vw,380px)] overflow-hidden rounded-2xl border border-border bg-card shadow-2xl outline-none"
              role="dialog"
              aria-modal="true"
              aria-label="Notification center"
            >
              {/* Header */}
              <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold">Notifications</h2>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-danger/10 px-1.5 py-0.5 text-[10px] font-bold text-danger">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={markAllRead} title="Mark all as read"
                    className="grid size-7 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground">
                    <Check className="size-4" />
                  </button>
                  <button onClick={clearAll} title="Clear all"
                    className="grid size-7 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground">
                    <Trash2 className="size-4" />
                  </button>
                  <button onClick={() => setOpen(false)} title="Close"
                    className="grid size-7 place-items-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground">
                    <X className="size-4" />
                  </button>
                </div>
              </div>

              {/* Browser-notification opt-in */}
              {permission !== "granted" && permission !== "unsupported" && (
                <button onClick={requestBrowserPermission}
                  className="flex w-full items-center gap-2 bg-primary/5 px-4 py-2 text-left text-xs font-medium text-primary hover:bg-primary/10">
                  <BellRing className="size-3.5" /> Enable desktop alerts for high-risk fraud
                </button>
              )}

              {/* Filters */}
              <div className="flex flex-wrap gap-1 px-3 py-2">
                {FILTERS.map((f) => (
                  <button key={f} onClick={() => setFilter(f)} aria-pressed={filter === f}
                    className={cn(
                      "rounded-full px-2.5 py-1 text-[11px] font-medium capitalize transition-colors",
                      filter === f ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-secondary",
                    )}>
                    {f}
                  </button>
                ))}
              </div>

              {/* List */}
              <div className="max-h-[46vh] overflow-y-auto">
                {shown.length === 0 ? (
                  <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
                    <Bell className="size-6 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      {filter === "all" ? "No notifications yet." : `No ${filter} notifications.`}
                    </p>
                  </div>
                ) : (
                  <ul className="divide-y divide-border/50">
                    <AnimatePresence initial={false}>
                      {shown.map((n) => {
                        const s = PRIORITY_STYLE[n.priority];
                        const Icon = s.Icon;
                        return (
                          <motion.li
                            key={n.id}
                            layout
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0 }}
                            className={cn("flex items-start gap-3 px-4 py-3", !n.read && "bg-primary/[0.03]")}
                          >
                            <Icon className={cn("mt-0.5 size-4 shrink-0", s.text)} />
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium text-foreground/90">{n.title}</p>
                                {!n.read && <span className="size-1.5 shrink-0 rounded-full bg-primary" />}
                              </div>
                              <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{n.body}</p>
                              <p className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground/70">
                                {n.priority} · {ago(n.ts)}
                              </p>
                            </div>
                          </motion.li>
                        );
                      })}
                    </AnimatePresence>
                  </ul>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
