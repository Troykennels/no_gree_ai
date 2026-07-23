"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BrainCircuit,
  CreditCard,
  Database,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  Menu,
  MessageSquareWarning,
  Radar,
  ScanLine,
  ScrollText,
  Search,
  Settings,
  Shield,
  ShieldCheck,
  X,
  type LucideIcon,
} from "lucide-react";
import { api, tokenStore } from "@/lib/api";
import { useLiveData } from "@/lib/live-provider";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./theme-toggle";
import { NotificationMenu } from "@/components/notifications/notification-menu";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}
interface NavGroup {
  label: string;
  items: NavItem[];
  adminOnly?: boolean;
}

const NAV: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/monitor", label: "Live Monitor", icon: Radar },
    ],
  },
  {
    label: "Detection",
    items: [
      { href: "/intelligence", label: "Fraud Intelligence", icon: BrainCircuit },
      { href: "/scam", label: "Scam Check", icon: MessageSquareWarning },
      { href: "/transaction", label: "Transaction Scoring", icon: CreditCard },
      { href: "/detector", label: "Quick Scan", icon: ScanLine },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/settings", label: "Settings", icon: Settings },
      { href: "/privacy", label: "Privacy Centre", icon: ShieldCheck },
      { href: "/help", label: "Help Centre", icon: LifeBuoy },
    ],
  },
  {
    label: "Admin",
    adminOnly: true,
    items: [
      { href: "/admin", label: "Admin Overview", icon: Shield },
      { href: "/admin/datasets", label: "Datasets", icon: Database },
      { href: "/admin/audit-logs", label: "Audit Logs", icon: ScrollText },
    ],
  },
];

function isActive(pathname: string, href: string) {
  if (href === "/admin") return pathname === "/admin";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() ?? "";
  const [open, setOpen] = useState(false);

  // Close the mobile drawer on navigation.
  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="app">
      <Sidebar open={open} onClose={() => setOpen(false)} pathname={pathname} />
      <div className={cn("scrim", open && "show")} onClick={() => setOpen(false)} aria-hidden />
      <div className="main">
        <Topbar onMenu={() => setOpen(true)} />
        <div className="content">{children}</div>
      </div>
    </div>
  );
}

function Sidebar({
  open,
  onClose,
  pathname,
}: {
  open: boolean;
  onClose: () => void;
  pathname: string;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const hasToken = mounted && !!tokenStore.get();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: hasToken, retry: false });
  const isAdmin = me.data?.role === "admin";

  return (
    <aside className={cn("sidebar", open && "open")}>
      {/* Brand */}
      <div className="brand">
        <Link href="/dashboard" aria-label="No_Gree AI dashboard" className="brand" style={{ padding: 0, border: 0, gap: 11 }}>
          <span className="logo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.jpg" alt="No_Gree AI" />
          </span>
          <span className="txt">
            <b>No_Gree AI</b>
            <span>Fraud Intelligence</span>
          </span>
        </Link>
        <button className="x" onClick={onClose} aria-label="Close menu">
          <X />
        </button>
      </div>

      {/* Nav */}
      <nav className="nav">
        {NAV.filter((g) => !g.adminOnly || isAdmin).map((group) => (
          <div className="group" key={group.label}>
            <p className="group-label">{group.label}</p>
            {group.items.map((item) => {
              const active = isActive(pathname, item.href);
              const Icon = item.icon;
              return (
                <Link key={item.href} href={item.href} className={cn(active && "active")}>
                  <Icon />
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Foot: user */}
      <div className="side-foot">
        <UserBlock me={me} hasToken={hasToken} onNavigate={onClose} />
      </div>
    </aside>
  );
}

function UserBlock({
  me,
  hasToken,
  onNavigate,
}: {
  me: ReturnType<typeof useQuery<Awaited<ReturnType<typeof api.me>>>>;
  hasToken: boolean;
  onNavigate: () => void;
}) {
  const router = useRouter();
  const authed = hasToken && me.isSuccess;

  if (!authed) {
    return (
      <div style={{ display: "flex", gap: 8 }}>
        <Link href="/login" onClick={onNavigate} className="btn" style={{ padding: "9px 12px", fontSize: 13 }}>
          Log in
        </Link>
        <Link href="/register" onClick={onNavigate} className="btn primary" style={{ padding: "9px 12px", fontSize: 13 }}>
          Sign up
        </Link>
      </div>
    );
  }

  const user = me.data;
  const initial = (user?.full_name ?? "?").slice(0, 1).toUpperCase();

  function logout() {
    tokenStore.clear();
    onNavigate();
    router.push("/");
  }

  return (
    <div className="user">
      <span className="avatar">{initial}</span>
      <div className="who">
        {user?.full_name}
        <small>{user?.email}</small>
      </div>
      <button className="out" onClick={logout} aria-label="Log out" title="Log out">
        <LogOut />
      </button>
    </div>
  );
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const router = useRouter();
  const { connected } = useLiveData();
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // ⌘K / Ctrl+K focuses the quick-scan search.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    router.push(q ? `/detector?q=${encodeURIComponent(q)}` : "/detector");
  }

  return (
    <header className="topbar">
      <button className="hamburger" onClick={onMenu} aria-label="Open menu">
        <Menu />
      </button>

      <form className="search" onSubmit={submitSearch}>
        <Search />
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Scan a message or transaction…"
          aria-label="Quick scan"
        />
        <kbd>⌘K</kbd>
      </form>

      <div className="top-right">
        <span className="livebadge">
          <span className="dot-live" />
          <span>{connected ? "Live" : "Protected"}</span>
        </span>
        <NotificationMenu />
        <ThemeToggle />
      </div>
    </header>
  );
}
