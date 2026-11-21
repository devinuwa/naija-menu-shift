"""Optional AI illustration for a hospital recommendation's top alternative.

Reuses the tree's existing image contracts: the prompt is a
``visual_preview.PreviewDraft`` and generation goes through
``bedrock_image.TitanImageGenerator`` (Titan V2, organiser-approved access
only, via ``workshop_generation_enabled``). Generation is attempted only
when the AI mode is Bedrock (``MENUSHIFT_AI_MODE=bedrock``). In local
mode - or when generation cannot run or fails - the caller shows no
image at all, never a stock or substitute picture.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .ai_config import AIConfig, get_ai_config
from .bedrock_image import (
    TITAN_IMAGE_MODEL_ID,
    GeneratedPreview,
    TitanImageGenerator,
    workshop_generation_enabled,
)
from .visual_preview import PreviewDraft

IMAGE_CAPTION = (
    "AI-generated illustration - how the alternative could look. "
    "It is not a photo of the actual dish."
)

_METHOD_PHRASES = {
    "grill": "grilled",
    "fry": "pan-fried",
    "boil": "boiled",
    "soup": "served in a soup pot",
    "steam": "steamed",
}


@dataclass(frozen=True)
class AlternativeImage:
    """Outcome of one illustration attempt.

    status "off" - local AI mode: the UI shows nothing.
    status "unavailable" - Bedrock mode, but generation could not run
    (image gates unset, client construction failed, or the model call
    failed): the UI shows a short note, never a substitute image.
    status "shown" - preview carries the generated image bytes.
    """

    status: str  # shown | unavailable | off
    preview: GeneratedPreview | None = None


def build_alternative_draft(
    dish_name: str, protein_name: str, method: str | None = None,
) -> PreviewDraft:
    """Constrained visual brief for the recommended alternative.

    Built only from the dish, the winning protein and the cooking
    method, in Nigerian food-presentation terms. The model illustrates
    the recommendation; it never changes it.
    """
    method_phrase = _METHOD_PHRASES.get(method or "", "")
    method_part = f", {method_phrase}" if method_phrase else ""
    prompt = (
        f"Photorealistic food concept of {dish_name} made with "
        f"{protein_name} as the protein{method_part}, presented the "
        "Nigerian way on a plain plate in a clean hospital kitchen, "
        "soft natural light, one modest portion, realistic texture, "
        "documentary food photography. Illustrative concept only."
    )
    negative = (
        "animal meat, beef, chicken, fish, extra unlisted ingredients, "
        "text, logos, watermark, people, hands"
    )
    recipe_id = re.sub(
        r"[^a-z0-9]+", "-", f"{dish_name}-{protein_name}".lower(),
    ).strip("-")[:80]
    return PreviewDraft(
        recipe_id=recipe_id or "hospital-alternative",
        prompt=prompt,
        negative_prompt=negative,
        interpreted_preferences=(),
        label=IMAGE_CAPTION,
    )


def generate_alternative_image(
    dish_name: str,
    protein_name: str,
    method: str | None = None,
    *,
    config: AIConfig | None = None,
    generator: TitanImageGenerator | None = None,
) -> AlternativeImage:
    """Generate the illustration for one recommendation, or report why not.

    Never raises: any configuration, construction or model failure in
    Bedrock mode is reported as "unavailable" so the recommendation page
    is never broken by the optional image.
    """
    if config is None:
        try:
            config = get_ai_config()
        except ValueError:
            return AlternativeImage(status="off")
    if not config.bedrock_enabled:
        return AlternativeImage(status="off")
    draft = build_alternative_draft(dish_name, protein_name, method)
    try:
        if generator is None:
            if not workshop_generation_enabled():
                return AlternativeImage(status="unavailable")
            generator = TitanImageGenerator(
                model_id=os.environ.get(
                    "BEDROCK_IMAGE_MODEL_ID", TITAN_IMAGE_MODEL_ID),
                region=config.aws_region,
                approved=True,
            )
        preview = generator.generate(draft)
    except Exception:  # noqa: BLE001 - the image must never break the page
        return AlternativeImage(status="unavailable")
    return AlternativeImage(status="shown", preview=preview)
