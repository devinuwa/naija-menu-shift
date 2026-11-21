"""Optional image generation adapter; disabled unless organisers explicitly approve it.

The official Hack the Fork AWS participant guide lists Titan *embeddings*
but NOT Titan Image Generator as an enabled workshop model. Do not invoke
image generation in the workshop without written approval and tested access.

Amazon Nova Canvas reached end of life in September 2026 and is not supported.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
from dataclasses import dataclass
from typing import Any

from .visual_preview import PreviewDraft

TITAN_IMAGE_MODEL_ID = "amazon.titan-image-generator-v2:0"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def workshop_generation_enabled() -> bool:
    """Two explicit opt-ins: feature gate and event-level model authorisation."""
    return (
        os.getenv("ENABLE_BEDROCK_IMAGE_PREVIEW") == "true"
        and os.getenv("IMAGE_MODEL_ORGANIZER_APPROVED") == "true"
        and os.getenv("BEDROCK_IMAGE_MODEL_ID") == TITAN_IMAGE_MODEL_ID
    )


@dataclass(frozen=True)
class GeneratedPreview:
    content: bytes
    mime_type: str
    model_id: str
    draft: PreviewDraft


class TitanImageGenerator:
    """Bedrock InvokeModel implementation for *approved* Titan V2 access only."""

    def __init__(
        self, *, model_id: str, region: str = "us-east-1",
        client: Any | None = None, approved: bool = False,
    ):
        if not approved:
            raise PermissionError("Image model access requires organiser approval")
        if region != "us-east-1":
            raise ValueError("Workshop AWS region must be us-east-1")
        if model_id != TITAN_IMAGE_MODEL_ID:
            raise ValueError("Unsupported image model; check the actual event allowlist")
        if client is None:
            try:
                import boto3  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError("Install optional dependency: pip install -e '.[aws]'") from exc
            client = boto3.client("bedrock-runtime", region_name=region)
        self.client = client
        self.model_id = model_id

    def generate(self, draft: PreviewDraft, *, seed: int = 42) -> GeneratedPreview:
        if not 0 <= seed <= 2147483647:
            raise ValueError("Seed out of range")
        if len(draft.prompt) > 512 or len(draft.negative_prompt) > 512:
            raise ValueError("Image prompt too large")
        payload = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": draft.prompt,
                "negativeText": draft.negative_prompt,
            },
            "imageGenerationConfig": {
                "quality": "standard",
                "numberOfImages": 1,
                "height": 512,
                "width": 512,
                "seed": seed,
            },
        }
        response = self.client.invoke_model(
            modelId=self.model_id, contentType="application/json",
            accept="application/json", body=json.dumps(payload),
        )
        try:
            data = json.loads(response["body"].read())
            encoded = data["images"][0]
            decoded = base64.b64decode(encoded, validate=True)
        except (KeyError, IndexError, TypeError, ValueError, binascii.Error) as exc:
            raise ValueError("Image model returned an invalid response") from exc
        if not decoded or len(decoded) > MAX_IMAGE_BYTES:
            raise ValueError("Image model returned an empty or oversized image")
        if decoded.startswith(b"\x89PNG\r\n\x1a\n"):
            mimetype = "image/png"
        elif decoded.startswith(b"\xff\xd8\xff"):
            mimetype = "image/jpeg"
        else:
            raise ValueError("Model returned unsupported image bytes")
        return GeneratedPreview(decoded, mimetype, self.model_id, draft)
