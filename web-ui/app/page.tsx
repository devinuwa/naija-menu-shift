import Link from "next/link";
import Studio from "@/components/Studio";
import MenuExplorer from "@/components/MenuExplorer";

export default function HomePage() {
  return (
    <div className="ns-shell">
      <header className="ns-header">
        <p className="ns-wordmark">Naija MenuShift</p>
      </header>

      <section className="ns-hero">
        <h1>Plant-based versions of familiar Nigerian dishes — costed, constrained, explainable.</h1>
        <p className="ns-hero-purpose">
          Naija MenuShift turns dishes a kitchen already serves into credible plant-based
          versions. Name a dish, and the tool tests plant proteins against hard
          constraints — protein target, cost per serving, allergens (fail-closed),
          cooking method, prep time and equipment — then ranks the survivors with the
          reasoning shown, including why the others were rejected.
        </p>
        <p className="ns-hero-purpose">
          It works for a single dish, a whole menu, and hospital menus — including
          condition-aware drafts for cardiovascular, kidney, hypertension and diabetes
          care, prepared for a dietitian to review and sign off. An AI proposer suggests
          candidates, but a deterministic safety gate checks every suggestion before it
          is shown.
        </p>
        <p className="ns-hero-cta-row">
          <Link className="ns-hero-cta" href="/hospital">
            Open the Hospital Menu Studio →
          </Link>
          <span className="ns-hero-cta-note">
            The ward menu board: plant-protein meals for every patient group,
            approved by the dietitian or doctor who orders the diet.
          </span>
        </p>
      </section>

      <main>
        <Studio />
        <MenuExplorer />
      </main>

      <footer className="ns-footer">
        <p>
          Naija MenuShift — a bounded, explainable decision tool. A model may propose;
          only the deterministic constraint engine decides. Beef appears as a comparison
          reference only and is never recommended.
        </p>
      </footer>
    </div>
  );
}
