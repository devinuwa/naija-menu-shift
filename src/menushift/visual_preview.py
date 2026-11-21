"""Source-aware visual briefs for concept images beside kitchen trial recipes.

Generated images are illustrative, not observations of the actual prepared food.
The model is never allowed to choose or alter ingredients. Presentation requests
are interpreted using a small, explicit visual vocabulary rather than injecting
raw user text into model instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .kitchen_optimizer import RecipeCandidate
from .visual_intent import VisualIntent

STYLES = {
    "Street-food": "Nigerian street-food presentation on clean brown serving paper",
    "Restaurant": "elegant restaurant plating on a plain white ceramic plate",
    "Cookbook": "simple home cookbook plating on a neutral plate",
}
METHODS = {
    "awara_firm": "firm awara cubes with light grill marks",
    "awara_pressed": "pressed awara cubes with light grill marks",
    "awara_frozen": "freeze-thawed awara cubes with a textured surface and light grill marks",
    "awara_fried": "pan-fried awara cubes with a golden crust",
}
PLATING_CUES = {
    "white plate": "white ceramic plate",
    "dark plate": "matte dark plate",
    "wooden board": "clean wooden serving board",
    "banana leaf": "banana leaf used only as serving surface",
}
CAMERA_CUES = {
    "overhead": "overhead photograph",
    "top down": "overhead photograph",
    "close up": "close-up photograph",
    "side view": "side-angle photograph",
}
LIGHTING_CUES = {
    "sunset": "warm evening light",
    "golden hour": "warm evening light",
    "evening": "warm evening light",
    "studio lighting": "clean studio light",
    "bright studio": "clean studio light",
    "daylight": "soft natural window light",
}
SETTING_CUES = {
    "roadside": "casual Nigerian street-food setting",
    "street stall": "casual Nigerian street-food setting",
    "outdoor food stand": "casual Nigerian street-food setting",
    "home kitchen": "simple home kitchen tabletop",
    "fine dining": "elegant restaurant tabletop",
    "minimal background": "neutral uncluttered background",
}


LABEL = "AI-generated illustrative concept — actual cooked appearance may differ."


@dataclass(frozen=True)
class PreviewDraft:
    recipe_id: str
    prompt: str
    negative_prompt: str
    interpreted_preferences: tuple[str, ...]
    label: str = LABEL

    @property
    def fingerprint(self) -> str:
        return sha256(
            (self.recipe_id + "\n" + self.prompt + "\n" + self.negative_prompt)
            .encode("utf-8")
        ).hexdigest()[:20]


def _visual_ingredients(candidate: RecipeCandidate) -> list[str]:
    ingredients = [x for x in candidate.ingredient_lines if x.purchase_g > 0]
    if not any(x.ingredient_id in {"wet_awara", "fried_awara"} for x in ingredients):
        raise ValueError("No evidenced tofu/awara ingredient")
    # Spices, salt and oil can affect preparation but do not justify depicting
    # elaborate yaji coatings or vegetables that aren't in the selected recipe.
    visible = []
    for row in ingredients:
        if row.ingredient_id == "onion":
            visible.append("a little onion")
        elif row.ingredient_id == "pepper":
            visible.append("fresh pepper")
    return visible


def build_preview_draft(
    candidate: RecipeCandidate, *,
    style: str = "Restaurant", restaurant_request: str = "",
    visual_intent: VisualIntent | None = None,
) -> PreviewDraft:
    """Build a constrained visual depiction of an already-feasible candidate."""
    if not candidate.eligible:
        raise ValueError("Cannot visually endorse an ineligible recipe")
    method = candidate.evaluation.option_id
    if method not in METHODS or style not in STYLES:
        raise ValueError("Unknown preparation method or visual presentation style")
    if not isinstance(restaurant_request, str) or len(restaurant_request) > 600:
        raise ValueError("Visual preference request must be at most 600 characters")

    request = restaurant_request.casefold()
    presentation = STYLES[style]
    interpreted = []
    for phrase, mapped in PLATING_CUES.items():
        if phrase in request:
            presentation = mapped
            interpreted.append(phrase)
            break
    angle = "natural close-up photograph"
    for phrase, mapped in CAMERA_CUES.items():
        if phrase in request:
            angle = mapped
            interpreted.append(phrase)
            break

    lighting = "soft natural window light"
    setting = "neutral uncluttered background"
    for phrase, mapped in LIGHTING_CUES.items():
        if phrase in request:
            lighting = mapped
            interpreted.append(phrase)
            break
    for phrase, mapped in SETTING_CUES.items():
        if phrase in request:
            setting = mapped
            interpreted.append(phrase)
            break
    if visual_intent is not None:
        if visual_intent.requires_recipe_change:
            raise ValueError(
                "Visual request asks to alter the ingredients; change and revalidate "
                "the recipe before generating a visual"
            )
        if visual_intent.style != "keep":
            presentation = STYLES[visual_intent.style]
        if visual_intent.plating != "default":
            presentation = visual_intent.plating
        if visual_intent.camera != "default":
            angle = visual_intent.camera
        if visual_intent.lighting != "default":
            lighting = visual_intent.lighting
        if visual_intent.setting != "default":
            setting = visual_intent.setting
        interpreted = list(visual_intent.interpretation)

    extras = _visual_ingredients(candidate)
    extras_part = ", with " + " and ".join(extras) if extras else ""
    prompt = (
        "Photorealistic food concept of Nigerian plant-based suya-inspired "
        f"{METHODS[method]}{extras_part}. "
        f"{presentation}, {angle}, {lighting}, {setting}. "
        "One modest portion; realistic irregular texture; documentary food "
        "photography. Only listed ingredients; illustrative, not tested."
    )
    negative = (
        "beef, animal meat, fish, peanut topping, heavy yaji coating, "
        "extra vegetables, unlisted sauces, garnish, text, logos, watermark, people"
    )
    if len(prompt) > 512 or len(negative) > 512:
        raise ValueError("Image model prompt exceeded allowed length")
    return PreviewDraft(
        recipe_id=candidate.identifier,
        prompt=prompt,
        negative_prompt=negative,
        interpreted_preferences=tuple(interpreted),
    )
