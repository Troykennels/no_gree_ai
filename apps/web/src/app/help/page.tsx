import type { Metadata } from "next";
import Link from "next/link";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Help Centre",
  description: "Answers to common questions about No Gree AI fraud detection.",
};

const STEPS = [
  { n: "1", t: "Paste a message or transaction", d: "Drop in any suspicious SMS, WhatsApp, POS or bank alert, or enter a transaction." },
  { n: "2", t: "Our AI scores it instantly", d: "Two models (scam text + transaction fraud) fuse into one 0-100 risk score." },
  { n: "3", t: "Get a clear plan", d: "See the reasons, a Safe/Suspicious/Scam verdict, and exactly what to do next." },
];

const FAQ = [
  { q: "Is No Gree AI free?", a: "Yes. Anyone can check a message with no account. Sign up (free) to save your history and get a personal dashboard." },
  { q: "Do you store my BVN, PIN or card number?", a: "Never in the clear. Those are automatically masked before anything is stored, shown, or streamed. See the Privacy Centre." },
  { q: "How accurate is it?", a: "Our scam detector scores ~99% on held-out messages and catches every common Nigerian scam type in our tests. No model is perfect, so always verify through your bank's official channel." },
  { q: "It flagged a real message as a scam. What now?", a: "Use the Safe/Scam buttons on the result. Your feedback trains the model to do better - that is the continuous-learning loop." },
  { q: "Can my bank or fintech integrate this?", a: "Yes. The platform is API-first. Contact us about webhook ingestion for real-time transaction scoring." },
  { q: "What should I do if I've been scammed?", a: "Freeze your card in your banking app, call your bank on the number printed on the card, and report to the NFIU. Do not call any number inside a suspicious message." },
];

export default function HelpPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-4xl">
        <PageHeader
          eyebrow="Support"
          title="Help Centre"
          description="Everything you need to get the most out of No Gree AI."
        />

        {/* How it works */}
        <div className="grid gap-4 sm:grid-cols-3">
          {STEPS.map((s) => (
            <Card key={s.n} className="p-6">
              <span className="grid size-9 place-items-center rounded-xl bg-primary/10 font-display text-lg font-bold text-primary">
                {s.n}
              </span>
              <h2 className="mt-4 font-semibold">{s.t}</h2>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{s.d}</p>
            </Card>
          ))}
        </div>

        {/* FAQ */}
        <h2 className="mb-4 mt-10 font-display text-xl font-bold">Frequently asked questions</h2>
        <div className="space-y-3">
          {FAQ.map((f) => (
            <details key={f.q} className="group rounded-2xl border border-border bg-card p-5">
              <summary className="flex cursor-pointer list-none items-center justify-between font-medium">
                {f.q}
                <span className="ml-4 text-muted-foreground transition-transform group-open:rotate-45">+</span>
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{f.a}</p>
            </details>
          ))}
        </div>

        {/* Contact */}
        <Card className="mt-10 flex flex-col items-center gap-3 p-8 text-center mesh">
          <h2 className="font-display text-xl font-bold">Still need help?</h2>
          <p className="max-w-md text-sm text-muted-foreground">
            Our team is here. Reach out and we will get back to you quickly.
          </p>
          <div className="mt-2 flex flex-wrap justify-center gap-2">
            <a href="mailto:support@nogree.ai">
              <Button>Email support</Button>
            </a>
            <Link href="/intelligence">
              <Button variant="outline">Try the detector</Button>
            </Link>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
