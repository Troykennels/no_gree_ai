"use client";

import {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState,
} from "react";
import { usePathname } from "next/navigation";
import { api, automationStreamUrl } from "./api";
import { makeDemoState } from "./demo-data";
import type { AutomationState, NotificationPriority, StreamEvent } from "./types";

// Routes that consume live fraud data. Marketing ("/"), "/login" and "/register"
// are deliberately excluded so no SSE/polling connection is opened there.
const LIVE_ROUTE_PREFIXES = [
  "/monitor", "/dashboard", "/intelligence", "/scam", "/transaction", "/detector", "/admin",
];

export interface AppNotification {
  id: string;
  priority: NotificationPriority;
  title: string;
  body: string;
  ts: number;
  read: boolean;
  source: string;
}

export interface ToastItem {
  id: string;
  priority: NotificationPriority;
  title: string;
  body: string;
}

interface LiveContextValue {
  state: AutomationState | null;
  connected: boolean;
  demo: boolean;
  setDemo: (on: boolean) => void;
  notifications: AppNotification[];
  unreadCount: number;
  toasts: ToastItem[];
  permission: NotificationPermission | "unsupported";
  requestBrowserPermission: () => void;
  markAllRead: () => void;
  markRead: (id: string) => void;
  clearAll: () => void;
  dismissToast: (id: string) => void;
}

const LiveContext = createContext<LiveContextValue | null>(null);

export function useLiveData(): LiveContextValue {
  const ctx = useContext(LiveContext);
  if (!ctx) throw new Error("useLiveData must be used within <LiveDataProvider>");
  return ctx;
}

const STORAGE_KEY = "nogree.notifications.v1";
const MAX_HISTORY = 100;
const TOAST_MS = 6000;
const MAX_TOASTS = 4;
const BROWSER_MIN_GAP_MS = 4000;

function uid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

export function LiveDataProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AutomationState | null>(null);
  const [connected, setConnected] = useState(false);
  // Client-side demo: local to this browser only, so it never affects other users.
  const [demo, setDemoFlag] = useState(false);
  const [demoSnapshot, setDemoSnapshot] = useState<AutomationState | null>(null);
  const setDemo = useCallback((on: boolean) => {
    setDemoFlag(on);
    setDemoSnapshot(on ? makeDemoState() : null);
  }, []);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [permission, setPermission] = useState<NotificationPermission | "unsupported">("unsupported");

  const pathname = usePathname();
  const isLiveRoute = !!pathname && LIVE_ROUTE_PREFIXES.some((p) => pathname.startsWith(p));

  const toastTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const lastBrowserNotify = useRef(0);
  const loaded = useRef(false);

  // Load persisted history + current permission once.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setNotifications(JSON.parse(raw) as AppNotification[]);
    } catch {
      /* ignore corrupt storage */
    }
    if (typeof Notification !== "undefined") setPermission(Notification.permission);
    loaded.current = true;
  }, []);

  // Persist history whenever it changes.
  useEffect(() => {
    if (!loaded.current) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications.slice(0, MAX_HISTORY)));
    } catch {
      /* quota / private mode - non-fatal */
    }
  }, [notifications]);

  const dismissToast = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
    const timer = toastTimers.current.get(id);
    if (timer) { clearTimeout(timer); toastTimers.current.delete(id); }
  }, []);

  const pushToast = useCallback((n: AppNotification) => {
    const toast: ToastItem = { id: n.id, priority: n.priority, title: n.title, body: n.body };
    setToasts((t) => [toast, ...t.filter((x) => x.id !== toast.id)].slice(0, MAX_TOASTS));
    toastTimers.current.set(n.id, setTimeout(() => dismissToast(n.id), TOAST_MS));
  }, [dismissToast]);

  const maybeBrowserNotify = useCallback((n: AppNotification) => {
    if (typeof Notification === "undefined" || Notification.permission !== "granted") return;
    if (n.priority !== "critical" && n.priority !== "danger") return;
    // Only when the tab isn't focused (don't nag while they're watching), rate-limited.
    if (typeof document !== "undefined" && document.visibilityState === "visible") return;
    const now = Date.now();
    if (now - lastBrowserNotify.current < BROWSER_MIN_GAP_MS) return;
    lastBrowserNotify.current = now;
    try {
      new Notification(`No_Gree AI · ${n.title}`, { body: n.body, tag: n.source });
    } catch {
      /* some browsers throw if not in a user gesture - ignore */
    }
  }, []);

  const addNotification = useCallback((n: AppNotification) => {
    setNotifications((list) => [n, ...list].slice(0, MAX_HISTORY));
    // Toast threats + system events; silence routine "safe" (info) items to the center.
    if (n.priority !== "info" || n.source === "report" || n.source === "security") pushToast(n);
    maybeBrowserNotify(n);
  }, [pushToast, maybeBrowserNotify]);

  const applyEvent = useCallback((evt: StreamEvent) => {
    switch (evt.type) {
      case "state":
        setState(evt.state);
        break;
      case "notification": {
        const p = evt.notification;
        if (!p) break;
        addNotification({
          id: uid(), priority: p.priority, title: p.title, body: p.body,
          ts: Date.now(), read: false, source: evt.item?.kind ?? "engine",
        });
        break;
      }
      case "security_score": {
        if (!evt.delta) break;
        const improved = evt.delta > 0;
        addNotification({
          id: uid(), priority: improved ? "info" : "warning",
          title: improved ? "Security Score improved" : "Security Score dropped",
          body: `Now ${Math.round(evt.score)}/100 (grade ${evt.grade})`,
          ts: Date.now(), read: false, source: "security",
        });
        break;
      }
      case "report_ready":
        addNotification({
          id: uid(), priority: "info", title: "Daily report generated",
          body: evt.report?.headline ?? "Your security report is ready.",
          ts: Date.now(), read: false, source: "report",
        });
        break;
      default:
        break;
    }
  }, [addNotification]);

  // Single SSE connection, opened only on routes that show live data (with a
  // snapshot-polling fallback). Marketing/auth pages open nothing.
  useEffect(() => {
    if (!isLiveRoute) return;

    let es: EventSource | null = null;
    let poll: ReturnType<typeof setInterval> | null = null;
    let cancelled = false;

    const stopPolling = () => { if (poll) { clearInterval(poll); poll = null; } };
    const startPolling = () => {
      if (poll) return;
      poll = setInterval(async () => {
        try { const snap = await api.automationSnapshot(); if (!cancelled) setState(snap); }
        catch { /* keep trying */ }
      }, 4000);
    };

    try {
      es = new EventSource(automationStreamUrl());
      es.onopen = () => { setConnected(true); stopPolling(); }; // live again -> drop the poll
      es.onmessage = (e) => {
        try { applyEvent(JSON.parse(e.data) as StreamEvent); } catch { /* bad frame */ }
      };
      es.onerror = () => { setConnected(false); startPolling(); };
    } catch {
      startPolling();
    }

    api.automationSnapshot().then((s) => { if (!cancelled) setState((p) => p ?? s); }).catch(() => {});

    return () => { cancelled = true; es?.close(); stopPolling(); };
  }, [applyEvent, isLiveRoute]);

  const markAllRead = useCallback(() => setNotifications((l) => l.map((n) => ({ ...n, read: true }))), []);
  const markRead = useCallback((id: string) =>
    setNotifications((l) => l.map((n) => (n.id === id ? { ...n, read: true } : n))), []);
  const clearAll = useCallback(() => setNotifications([]), []);
  const requestBrowserPermission = useCallback(() => {
    if (typeof Notification === "undefined") { setPermission("unsupported"); return; }
    Notification.requestPermission().then((p) => setPermission(p)).catch(() => {});
  }, []);

  const unreadCount = useMemo(() => notifications.filter((n) => !n.read).length, [notifications]);

  const value = useMemo<LiveContextValue>(() => ({
    state: demo ? demoSnapshot : state,
    connected, demo, setDemo, notifications, unreadCount, toasts, permission,
    requestBrowserPermission, markAllRead, markRead, clearAll, dismissToast,
  }), [state, demo, demoSnapshot, setDemo, connected, notifications, unreadCount, toasts, permission,
      requestBrowserPermission, markAllRead, markRead, clearAll, dismissToast]);

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}
