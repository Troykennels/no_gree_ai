import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "No_Gree AI - Fraud Intelligence",
    template: "%s · No_Gree AI",
  },
  description:
    "No_Gree AI - intelligent fraud detection and risk intelligence that protects Nigerians from fake bank SMS, WhatsApp scams, POS fraud and fake loan offers, before money is lost. Detect. Protect. Prevent.",
  keywords: [
    "Nigeria fraud detection",
    "fake bank SMS",
    "scam checker",
    "fraud AI",
    "risk intelligence",
    "phishing",
  ],
  icons: {
    icon: "/logo.jpg",
    apple: "/logo.jpg",
  },
  openGraph: {
    title: "No_Gree AI - Fraud Intelligence",
    description:
      "Paste any suspicious message and get an instant AI fraud verdict with a clear explanation. Detect. Protect. Prevent.",
    type: "website",
  },
};

// Applied before hydration to avoid a theme flash. Defaults to LIGHT (white),
// matching the design mockup; dark is opt-in via the toggle.
const themeScript = `
(function(){
  try {
    var t = localStorage.getItem('nogree.theme');
    if (t === 'dark') { document.documentElement.classList.add('dark'); }
    else { document.documentElement.classList.remove('dark'); }
  } catch (e) { document.documentElement.classList.remove('dark'); }
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
