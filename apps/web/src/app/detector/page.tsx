import type { Metadata } from "next";
import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { Detector } from "@/components/detector/detector";

export const metadata: Metadata = {
  title: "Fraud Detector",
  description:
    "Paste any suspicious message and get an instant AI fraud verdict with an explanation.",
};

export default function DetectorPage() {
  return (
    <>
      <Navbar />
      <main className="pt-28 pb-20 mesh">
        <div className="container max-w-3xl">
          <div className="mb-8 text-center">
            <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Is this message a scam?
            </h1>
            <p className="mt-3 text-muted-foreground">
              Paste the SMS, WhatsApp message, POS alert or loan offer you&apos;re
              unsure about. SecureNaija will tell you the fraud risk and why.
            </p>
          </div>
          <Detector />
          <p className="mt-6 text-center text-xs text-muted-foreground">
            SecureNaija gives guidance, not financial or legal advice. When in
            doubt, contact your bank through its official channels.
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
