"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Logo } from "./logo";
import { Button } from "@/components/ui/button";
import { NotificationMenu } from "@/components/notifications/notification-menu";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/monitor", label: "Dashboard" },
  { href: "/intelligence", label: "Intelligence" },
  { href: "/scam", label: "Scam check" },
  { href: "/transaction", label: "Transactions" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled ? "border-b border-border/60 glass" : "bg-transparent",
      )}
    >
      <nav className="container flex h-16 items-center justify-between">
        <Link href="/" aria-label="SecureNaija home">
          <Logo />
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <NotificationMenu />
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Log in
            </Button>
          </Link>
          <Link href="/intelligence">
            <Button size="sm">Try it free</Button>
          </Link>
        </div>

        <div className="flex items-center gap-1 md:hidden">
          <NotificationMenu />
          <button
            className="grid h-10 w-10 place-items-center rounded-lg"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
            aria-expanded={open}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-border/60 glass md:hidden">
          <div className="container flex flex-col gap-1 py-4">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
              >
                {l.label}
              </Link>
            ))}
            <div className="mt-2 flex gap-2">
              <Link href="/login" className="flex-1" onClick={() => setOpen(false)}>
                <Button variant="outline" className="w-full">
                  Log in
                </Button>
              </Link>
              <Link href="/intelligence" className="flex-1" onClick={() => setOpen(false)}>
                <Button className="w-full">Try it free</Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
