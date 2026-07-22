import type { Metadata } from "next";
import { Inter, Sora } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const sora = Sora({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["600", "700", "800"],
});

export const metadata: Metadata = {
  title: {
    default: "SecureNaija - Stop fraud before money is lost",
    template: "%s · SecureNaija",
  },
  description:
    "AI-powered fraud intelligence that protects Nigerians from fake bank SMS, WhatsApp scams, POS fraud and fake loan offers - before money is lost.",
  keywords: [
    "Nigeria fraud detection",
    "fake bank SMS",
    "scam checker",
    "fraud AI",
    "phishing",
  ],
  openGraph: {
    title: "SecureNaija - Stop fraud before money is lost",
    description:
      "Paste any suspicious message and get an instant AI fraud verdict with a clear explanation.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${sora.variable} dark`}>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
