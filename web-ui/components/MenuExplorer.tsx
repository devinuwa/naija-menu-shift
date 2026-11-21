import { MENU_EXPLORER_ITEMS } from "@/lib/data";

/**
 * Plant-based menu explorer — illustrative product-vision section inspired by
 * the real menu of Veggie Victory, Lagos (Nigeria's first vegan restaurant).
 * These items are NOT engine outputs and carry no costed formulation.
 */
export default function MenuExplorer() {
  return (
    <section className="ns-explorer" aria-labelledby="explorer-heading">
      <h2 id="explorer-heading" className="ns-panel-title">
        Plant-based menu explorer — the wider vision
      </h2>
      <p className="ns-note ns-explorer-note">
        Illustrative menu items only — not engine outputs and not costed formulations.
        Inspired by the real plant-based Nigerian menu at Veggie Victory, Lagos
        (Nigeria’s first vegan restaurant, est. 2013): proof that familiar dishes
        already have plant-based versions in the market. MenuShift’s job is to help
        any kitchen evaluate such shifts against its own budget, stock and equipment —
        starting with the sourced suya studio above.
      </p>
      <div className="ns-menu-grid">
        {MENU_EXPLORER_ITEMS.map((item) => (
          <article key={item.name} className="ns-menu-card">
            <p className="ns-card-kicker">{item.style}</p>
            <h3 className="ns-menu-name">{item.name}</h3>
            <p>{item.description}</p>
            <p className="ns-chip">Protein base: {item.proteinBase}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
