import type { Metadata } from "next";
import { AppShell } from "@/components/app/app-shell";
import { PageHeader } from "@/components/app/page-header";
import { Detector } from "@/components/detector/detector";

export const metadata: Metadata = {
  title: "Fraud Detector",
  description:
    "Paste any suspicious message and get an instant AI fraud verdict with an explanation.",
};

export default async function DetectorPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;

  return (
    <AppShell>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>
        <PageHeader
          eyebrow="Quick Scan · Message Fraud"
          title="Is this message a scam?"
          description="Paste the SMS, WhatsApp message, POS alert or loan offer you're unsure about. No_Gree AI will tell you the fraud risk and why."
        />
        <Detector initialMessage={q ?? ""} />
        <p className="footnote">
          No_Gree AI gives guidance, not financial or legal advice. When in doubt, contact your bank through its official channels.
        </p>
      </div>
    </AppShell>
  );
}
