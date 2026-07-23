"use client";

import { motion } from "framer-motion";
import {
  BadgeCheck,
  BrainCircuit,
  Building2,
  ClipboardPaste,
  CreditCard,
  Landmark,
  Link2,
  MessageSquareWarning,
  ScanSearch,
  ShieldCheck,
  Store,
  Users,
} from "lucide-react";
import { Card } from "@/components/ui/card";

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
};

const THREATS = [
  { icon: MessageSquareWarning, label: "Fake bank SMS" },
  { icon: Users, label: "WhatsApp scams" },
  { icon: CreditCard, label: "Fake POS alerts" },
  { icon: Landmark, label: "Fake loan offers" },
  { icon: Link2, label: "Phishing links" },
  { icon: BadgeCheck, label: "Fake investments" },
];

export function ProblemSection() {
  return (
    <section className="border-y border-border/60 bg-secondary/30 py-16">
      <div className="container">
        <motion.div {...fadeUp} className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Fraud in Nigeria moves faster than the banks can react
          </h2>
          <p className="mt-4 text-muted-foreground">
            Today&apos;s systems flag fraud <em>after</em> the money is gone.
            No_Gree AI flips that - catching the scam at the moment it lands in
            your inbox.
          </p>
        </motion.div>

        <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {THREATS.map((t, i) => (
            <motion.div
              key={t.label}
              {...fadeUp}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="flex flex-col items-center gap-2 p-4 text-center">
                <t.icon className="size-6 text-danger" />
                <span className="text-xs font-medium text-foreground/90">
                  {t.label}
                </span>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

const STEPS = [
  {
    icon: ClipboardPaste,
    title: "Paste the message",
    body: "Copy any suspicious SMS, WhatsApp text, POS alert or loan offer and drop it in.",
  },
  {
    icon: BrainCircuit,
    title: "AI reads the intent",
    body: "Our model, trained on Nigerian fraud patterns, scores the message in real time.",
  },
  {
    icon: ScanSearch,
    title: "Get an explained verdict",
    body: "See a clear risk score and the exact signals that raised - or lowered - the risk.",
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="py-20">
      <div className="container">
        <motion.div {...fadeUp} className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-primary">
            How it works
          </span>
          <h2 className="mt-2 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            From suspicion to certainty in seconds
          </h2>
        </motion.div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <motion.div key={s.title} {...fadeUp} transition={{ delay: i * 0.1 }}>
              <Card className="h-full p-7">
                <div className="mb-5 flex items-center gap-3">
                  <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
                    <s.icon className="size-5" />
                  </span>
                  <span className="text-4xl font-bold text-border">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                </div>
                <h3 className="text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{s.body}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

const FEATURES = [
  {
    icon: BrainCircuit,
    title: "Explainable AI",
    body: "Every verdict comes with the exact signals behind it - powered by SHAP, not a black box.",
  },
  {
    icon: ShieldCheck,
    title: "Nigeria-trained",
    body: "Tuned on local fraud typologies: BVN phishing, fake alerts, POS scams and loan bait.",
  },
  {
    icon: ScanSearch,
    title: "Real-time scoring",
    body: "Sub-second analysis so you can decide before you click, call or pay.",
  },
  {
    icon: CreditCard,
    title: "Built for scale",
    body: "A clean API that banks, fintechs and payment companies can plug straight into.",
  },
];

export function Features() {
  return (
    <section id="features" className="border-t border-border/60 bg-secondary/30 py-20">
      <div className="container">
        <motion.div {...fadeUp} className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-primary">
            Why No_Gree AI
          </span>
          <h2 className="mt-2 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Enterprise-grade fraud intelligence
          </h2>
        </motion.div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f, i) => (
            <motion.div key={f.title} {...fadeUp} transition={{ delay: i * 0.08 }}>
              <Card className="h-full p-6">
                <span className="grid size-11 place-items-center rounded-xl bg-primary/10 text-primary">
                  <f.icon className="size-5" />
                </span>
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.body}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

const AUDIENCES = [
  { icon: Users, label: "Citizens & Students" },
  { icon: Store, label: "Traders & SMEs" },
  { icon: Landmark, label: "Banks" },
  { icon: Building2, label: "Fintechs & PSPs" },
];

export function TrustSection() {
  return (
    <section id="trust" className="py-20">
      <div className="container">
        <div className="overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary/10 via-card to-card p-10 sm:p-14">
          <div className="mx-auto max-w-2xl text-center">
            <motion.h2
              {...fadeUp}
              className="font-display text-3xl font-bold tracking-tight sm:text-4xl"
            >
              Protecting everyone in the money chain
            </motion.h2>
            <motion.p {...fadeUp} className="mt-4 text-muted-foreground">
              From a student checking a scholarship SMS to a bank screening
              millions of messages - No_Gree AI scales with you.
            </motion.p>
          </div>

          <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {AUDIENCES.map((a, i) => (
              <motion.div
                key={a.label}
                {...fadeUp}
                transition={{ delay: i * 0.08 }}
                className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-background/50 p-6 text-center"
              >
                <a.icon className="size-7 text-primary" />
                <span className="text-sm font-medium">{a.label}</span>
              </motion.div>
            ))}
          </div>

          <p className="mt-10 text-center text-sm text-muted-foreground">
            🔒 No_Gree AI never asks for your BVN, OTP, PIN or bank password.
          </p>
        </div>
      </div>
    </section>
  );
}
