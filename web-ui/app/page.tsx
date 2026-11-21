import Studio from "@/components/Studio";
import MenuExplorer from "@/components/MenuExplorer";

export default function HomePage() {
  return (
    <div className="ns-shell">
      <header className="ns-header">
        <p className="ns-wordmark">Naija MenuShift</p>
        <p className="ns-header-sub">
          Vercel interface demo · Hack the Fork Nigeria 2026 · Challenge 2
        </p>
        <p><a href="https://naija-menushift.streamlit.app/" rel="noopener noreferrer">Open the complete Streamlit research application</a></p>
      </header>

      <section className="ns-hero">
        <h1>Plant-based versions of familiar Nigerian dishes — costed, constrained, explainable.</h1>
        <p className="ns-hero-purpose">
          For restaurant owners and caterers: find a viable <em>research formulation</em>{" "}
          for kitchen testing in under four steps — within your budget for listed partial
          costs, your protein target, your time, your equipment and your stock.
        </p>
        <div className="ns-warning" role="note">
          <strong>Research warning:</strong> this is a separate suya-focused synthetic demonstration, not the complete Python-backed multi-dish research application. Prices and
          nutrients are illustrative estimates from reference data, not verified market
          measurements, and no output is approved for food service. Unreviewed data is
          labelled at the point of decision.
        </div>
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
