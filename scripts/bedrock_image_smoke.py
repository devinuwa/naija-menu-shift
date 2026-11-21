"""Manual one-shot image smoke test ONLY after event organiser approval.

Never run inside the event AWS account until the team is explicitly granted
text-to-image permissions. AWS workshop guide currently does NOT list this model.
"""
from __future__ import annotations

import os
from pathlib import Path

from menushift.bedrock_image import (
    TITAN_IMAGE_MODEL_ID,
    TitanImageGenerator,
    workshop_generation_enabled,
)
from menushift.kitchen_optimizer import INVENTORY_ITEMS, explore
from menushift.visual_preview import build_preview_draft

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if not workshop_generation_enabled():
        raise SystemExit(
            "Image model is not confirmed by organisers. "
            "No AWS request was made; ask organisers for exact allowed model ID."
        )
    options = explore(
        ROOT / "data" / "sources",
        budget_ngn=2500, protein_target_g=8, max_prep_minutes=240,
        equipment=frozenset({"grill", "press", "frying_pan"}),
        available_ingredients=frozenset(INVENTORY_ITEMS),
        portions_g=(140,),
    )
    selected = options.best("budget")
    if selected is None:
        raise SystemExit("No feasible recipe; cannot generate")
    draft = build_preview_draft(selected, style="Restaurant")
    result = TitanImageGenerator(
        model_id=TITAN_IMAGE_MODEL_ID, approved=True
    ).generate(draft)
    out = Path(os.environ.get("IMAGE_PREVIEW_OUTPUT", "/tmp/naija-menushift-concept.png"))
    out.write_bytes(result.content)
    print(f"Saved one {result.mime_type} concept image to {out}")
    print("Illustrative only. Inspect ingredients manually; no appearance guarantee.")


if __name__ == "__main__":
    main()
