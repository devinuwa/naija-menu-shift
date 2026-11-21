import type { Metadata } from "next";
import Link from "next/link";
import HospitalStudio from "@/components/HospitalStudio";
import "./hospital.css";

export const metadata: Metadata = {
  title: "Naija MenuShift · Hospital Menu Studio",
  description:
    "An AI tool that helps Nigerian hospital kitchens adapt the meals they already cook — with plant proteins, and for patients' medical needs.",
};

export default function HospitalPage() {
  return (
    <div className="ns-shell">
      <header className="ns-header">
        <p className="ns-wordmark">Naija MenuShift</p>
        <p className="ns-header-sub">
          <Link href="/">← Kitchen Intelligence Studio</Link>
        </p>
      </header>

      <section className="hs-hero">
        <p className="hs-hero-eyebrow">Naija MenuShift · Hospital Menu Studio</p>
        <blockquote className="hs-hero-quote-big">
          <p>“Let food be thy medicine and medicine be thy food.”</p>
          <cite>— Hippocrates</cite>
        </blockquote>
        <p className="hs-hero-promise">
          An AI tool that helps Nigerian hospital kitchens adapt the meals they
          already cook — with plant proteins, and for patients&rsquo; medical
          needs.
        </p>
        <p className="hs-hero-stats">
          <span>
            <strong>14</strong> dishes on the ward menu
          </span>
          <span>
            <strong>7</strong> plant proteins
          </span>
          <span>
            <strong>4</strong> patient groups
          </span>
        </p>
      </section>

      <section className="hs-twothings" aria-labelledby="hs-does-title">
        <h2 id="hs-does-title" className="hs-display hs-section-title">
          What Naija MenuShift does
        </h2>
        <div className="hs-two-grid">
          <article className="hs-two-card">
            <h3 className="hs-display">Plant-protein swaps</h3>
            <p>
              It swaps costly meat with plant proteins people already eat —
              beans, soya, awara, groundnut — while keeping the protein.
            </p>
          </article>
          <article className="hs-two-card">
            <h3 className="hs-display">Condition-aware meals</h3>
            <p>
              It adjusts the same meal for patient groups: less salt and fat for
              heart patients, portions and fibre for diabetes, key nutrients
              flagged for kidney care.
            </p>
          </article>
        </div>
        <p className="hs-approval">
          Approved by: the dietitian or doctor who orders the diet.
        </p>
      </section>

      <main>
        <HospitalStudio />
      </main>

      <footer className="ns-footer">
        <p>
          Naija MenuShift — helping Nigerian hospital kitchens adapt the meals
          they already cook. Approved by: the dietitian or doctor who orders
          the diet.
        </p>
      </footer>
    </div>
  );
}
