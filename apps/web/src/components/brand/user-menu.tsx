"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import {
  Settings, ShieldCheck, LifeBuoy, LayoutDashboard, LogOut, ChevronDown, Shield,
} from "lucide-react";
import { api, tokenStore } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MENU = [
  { href: "/dashboard", label: "My dashboard", icon: LayoutDashboard },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/privacy", label: "Privacy Centre", icon: ShieldCheck },
  { href: "/help", label: "Help Centre", icon: LifeBuoy },
];

export function UserMenu({ onNavigate }: { onNavigate?: () => void }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);
  const hasToken = mounted && !!tokenStore.get();

  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: hasToken, retry: false });
  const authed = hasToken && me.isSuccess;
  const user = me.data;

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  function logout() {
    tokenStore.clear();
    setOpen(false);
    onNavigate?.();
    router.push("/");
  }

  if (!authed) {
    return (
      <>
        <Link href="/login" onClick={onNavigate}>
          <Button variant="ghost" size="sm">Log in</Button>
        </Link>
        <Link href="/register" onClick={onNavigate}>
          <Button size="sm">Get Started</Button>
        </Link>
      </>
    );
  }

  const initial = (user?.full_name ?? "?").slice(0, 1).toUpperCase();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 rounded-full py-1 pl-1 pr-2 transition-colors hover:bg-secondary"
        aria-label="Account menu"
        aria-expanded={open}
      >
        <span className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-primary to-emerald-400 text-sm font-bold text-primary-foreground">
          {initial}
        </span>
        <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden />
            <motion.div
              ref={panelRef}
              initial={{ opacity: 0, y: -6, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 z-50 mt-2 w-60 overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
              role="menu"
            >
              <div className="border-b border-border/60 px-4 py-3">
                <p className="truncate text-sm font-semibold">{user?.full_name}</p>
                <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
              </div>
              <div className="p-1.5">
                {MENU.map((m) => (
                  <Link key={m.href} href={m.href} onClick={() => { setOpen(false); onNavigate?.(); }}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 hover:bg-secondary">
                    <m.icon className="size-4 text-muted-foreground" /> {m.label}
                  </Link>
                ))}
                {user?.role === "admin" ? (
                  <Link href="/admin" onClick={() => { setOpen(false); onNavigate?.(); }}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-primary hover:bg-primary/10">
                    <Shield className="size-4" /> Admin
                  </Link>
                ) : null}
              </div>
              <div className="border-t border-border/60 p-1.5">
                <button onClick={logout}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-danger hover:bg-danger/10">
                  <LogOut className="size-4" /> Log out
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
