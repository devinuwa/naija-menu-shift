"""AI illustration for hospital recommendations: Bedrock-gated, fail-soft.

The illustration reuses the tree's image contracts (PreviewDraft in,
GeneratedPreview out). It is attempted only in Bedrock AI mode; local
mode shows nothing, and any failure in Bedrock mode degrades to a short
note on the page - never a substitute image and never an exception.
"""
from __future__ import annotations

import base64
from pathlib import Path

from menushift import hospital_image
from menushift.ai_config import AIConfig
from menushift.bedrock_image import GeneratedPreview
from menushift.hospital_image import (
    IMAGE_CAPTION,
    AlternativeImage,
    build_alternative_draft,
    generate_alternative_image,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages" / "3_Hospital_Menu.py"

# A real 1x1 PNG: Streamlit validates image bytes with PIL before display.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/"
    "q842iQAAAABJRU5ErkJggg=="
)

BEDROCK = AIConfig(mode="bedrock", bedrock_model_id="amazon.nova-pro-v1:0")
LOCAL = AIConfig(mode="local")


class FakeGenerator:
    """Stands in for TitanImageGenerator; records the drafts it was given."""

    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.drafts = []

    def generate(self, draft, *, seed: int = 42):
        self.drafts.append(draft)
        if self.fail:
            raise RuntimeError("model unavailable")
        return GeneratedPreview(
            PNG_BYTES, "image/png", "amazon.titan-image-generator-v2:0", draft)


def test_local_mode_never_generates():
    generator = FakeGenerator()
    outcome = generate_alternative_image(
        "Fish", "Awara (soy curd / tofu)", "soup",
        config=LOCAL, generator=generator)
    assert outcome.status == "off"
    assert outcome.preview is None
    assert generator.drafts == []  # the generator is never even called


def test_bedrock_mode_shows_the_generated_image():
    generator = FakeGenerator()
    outcome = generate_alternative_image(
        "Grilled beef skewers", "Awara (soy curd / tofu)", "grill",
        config=BEDROCK, generator=generator)
    assert outcome.status == "shown"
    assert outcome.preview is not None
    assert outcome.preview.content == PNG_BYTES
    draft = generator.drafts[0]
    # The prompt is built from the dish, the winning protein and the method.
    assert "Grilled beef skewers" in draft.prompt
    assert "Awara (soy curd / tofu)" in draft.prompt
    assert "grilled" in draft.prompt
    assert "Nigerian" in draft.prompt
    # The Titan contract caps prompts at 512 characters.
    assert len(draft.prompt) <= 512
    assert len(draft.negative_prompt) <= 512


def test_bedrock_generation_failure_is_unavailable_not_fatal():
    outcome = generate_alternative_image(
        "Fish", "Egusi (melon seed)", "soup",
        config=BEDROCK, generator=FakeGenerator(fail=True))
    assert outcome.status == "unavailable"
    assert outcome.preview is None


def test_bedrock_mode_without_image_gates_is_unavailable(monkeypatch):
    for var in ("ENABLE_BEDROCK_IMAGE_PREVIEW",
                "IMAGE_MODEL_ORGANIZER_APPROVED", "BEDROCK_IMAGE_MODEL_ID"):
        monkeypatch.delenv(var, raising=False)
    outcome = generate_alternative_image(
        "Fish", "Egusi (melon seed)", "soup", config=BEDROCK)
    assert outcome.status == "unavailable"
    assert outcome.preview is None


def test_draft_is_captioned_as_an_illustration():
    draft = build_alternative_draft("Meat", "Seitan (wheat gluten)")
    assert draft.label == IMAGE_CAPTION
    assert "AI-generated illustration" in IMAGE_CAPTION
    assert "not a photo" in IMAGE_CAPTION


# ----------------------------------------------------------------------
# Page wiring: the Hospital page asks hospital_image for the top
# alternative's illustration and renders exactly what it is told to.
# ----------------------------------------------------------------------

def _run_page(monkeypatch, outcome: AlternativeImage):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(
        hospital_image, "generate_alternative_image",
        lambda *args, **kwargs: outcome)
    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    return at


def test_hospital_page_shows_image_with_caption(monkeypatch):
    draft = build_alternative_draft("Fish", "Awara (soy curd / tofu)", "soup")
    preview = GeneratedPreview(
        PNG_BYTES, "image/png", "amazon.titan-image-generator-v2:0", draft)
    at = _run_page(monkeypatch, AlternativeImage(status="shown", preview=preview))
    captions = [c.value for c in at.caption]
    assert any("AI-generated illustration" in c for c in captions)
    assert not any("could not be generated" in c for c in captions)


def test_hospital_page_notes_failed_generation(monkeypatch):
    at = _run_page(monkeypatch, AlternativeImage(status="unavailable"))
    captions = [c.value for c in at.caption]
    assert any("could not be generated" in c for c in captions)
    assert not any("AI-generated illustration" in c for c in captions)


def test_hospital_page_local_mode_shows_no_image_block(monkeypatch):
    at = _run_page(monkeypatch, AlternativeImage(status="off"))
    captions = [c.value for c in at.caption]
    assert not any("AI-generated illustration" in c for c in captions)
    assert not any("could not be generated" in c for c in captions)
