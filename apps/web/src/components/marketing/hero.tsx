"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Detector } from "@/components/detector/detector";

export function Hero() {
  return (
    <section className="relative overflow-hidden pt-28 pb-16 mesh sm:pt-32">
      <div className="pointer-events-none absolute inset-0 grid-lines" />
      <div className="container relative grid items-center gap-12 lg:grid-cols-[1.05fr_1fr]">
        <div className="max-w-xl">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary"
          >
            <ShieldCheck className="size-3.5" />
            No Gree AI · Fraud intelligence for Nigeria
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.05 }}
            className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl"
          >
            Stop fraud <span className="text-gradient">before</span> the money
            leaves.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.12 }}
            className="mt-5 text-lg text-muted-foreground"
          >
            Millions of Nigerians lose money to fake bank SMS, WhatsApp scams,
            POS fraud and fake loans every year. No Gree AI reads any suspicious
            message and tells you if it&apos;s fraud - instantly, with reasons.
            <span className="mt-2 block font-semibold text-foreground">
              Detect. Protect. Prevent.
            </span>
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.18 }}
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Link href="/detector">
              <Button size="lg">
                Check a message <ArrowRight />
              </Button>
            </Link>
            <Link href="/#how">
              <Button size="lg" variant="outline">
                How it works
              </Button>
            </Link>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-8 flex items-center gap-6 text-sm text-muted-foreground"
          >
            <div>
              <span className="block text-xl font-bold text-foreground">
                &lt;1s
              </span>
              analysis time
            </div>
            <div className="h-8 w-px bg-border" />
            <div>
              <span className="block text-xl font-bold text-foreground">
                Explainable
              </span>
              every verdict
            </div>
            <div className="h-8 w-px bg-border" />
            <div>
              <span className="block text-xl font-bold text-foreground">
                Free
              </span>
              for citizens
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="mb-3 flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-pulse-ring rounded-full bg-primary" />
              <span className="relative inline-flex size-2 rounded-full bg-primary" />
            </span>
            Live fraud detector
          </div>
          <Detector compact />
        </motion.div>
      </div>
    </section>
  );
}
