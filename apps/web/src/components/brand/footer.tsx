import Link from "next/link";
import { Logo } from "./logo";

export function Footer() {
  return (
    <footer className="border-t border-border/60">
      <div className="container grid gap-10 py-14 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
        <div className="space-y-4">
          <Logo />
          <p className="max-w-xs text-sm text-muted-foreground">
            Intelligent fraud detection &amp; risk intelligence that protects
            Nigerians from digital fraud before money is lost.
          </p>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Detect. Protect. Prevent.
          </p>
        </div>

        {[
          {
            title: "Product",
            links: [
              ["Detector", "/detector"],
              ["Intelligence", "/intelligence"],
              ["Live dashboard", "/monitor"],
              ["How it works", "/#how"],
            ],
          },
          {
            title: "Support",
            links: [
              ["Help Centre", "/help"],
              ["Settings", "/settings"],
              ["Contact", "mailto:support@nogree.ai"],
            ],
          },
          {
            title: "Legal",
            links: [
              ["Privacy Centre", "/privacy"],
              ["Security", "/#trust"],
              ["NDPR", "/privacy"],
            ],
          },
        ].map((col) => (
          <div key={col.title} className="space-y-3">
            <h4 className="text-sm font-semibold">{col.title}</h4>
            <ul className="space-y-2">
              {col.links.map(([label, href]) => (
                <li key={label}>
                  <Link
                    href={href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-border/60">
        <div className="container flex flex-col items-center justify-between gap-2 py-6 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} No_Gree AI. All rights reserved.</p>
          <p>Built for Nigeria 🇳🇬 · Never share your BVN, OTP or PIN.</p>
        </div>
      </div>
    </footer>
  );
}
