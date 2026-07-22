import { Navbar } from "@/components/brand/navbar";
import { Footer } from "@/components/brand/footer";
import { Hero } from "@/components/marketing/hero";
import {
  Features,
  HowItWorks,
  ProblemSection,
  TrustSection,
} from "@/components/marketing/sections";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <ProblemSection />
        <HowItWorks />
        <Features />
        <TrustSection />
      </main>
      <Footer />
    </>
  );
}
