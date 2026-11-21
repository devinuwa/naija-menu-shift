"""Restricted, read-only field-data reviewer workspace.

Reviewers must collect actual package evidence, actual measured batches, and
consented anonymised sensory feedback. No uploads are persisted by this page.
Approval is a human workflow, not a claim that this software certifies food.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from menushift.food_evidence import (
    HEADER_GROUPS,
    FieldEvidence,
    audit_evidence,
    load_field_evidence,
    read_evidence_csv,
    sensory_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "data" / "evidence_intake"

st.set_page_config(page_title="Food evidence reviewer | Naija MenuShift", page_icon="🧪", layout="wide")
st.title("Kitchen evidence reviewer workspace")
st.caption("Team Sprout · source, ingredient-packaging, measured-batch and sensory review")
st.warning(
    "Research workflow only. A complete form or passing validator does not "
    "certify allergen safety, food handling, nutritional accuracy or consumer acceptance."
)

enabled = os.getenv("ENABLE_EVIDENCE_REVIEW_WORKSPACE") == "true"
access_key = os.getenv("EVIDENCE_REVIEW_ACCESS_CODE", "")
if not enabled or len(access_key) < 16:
    st.info(
        "Reviewer workspace is not configured. Ask the technical lead for "
        "the secure review process. No data is collected or stored here."
    )
    st.stop()

entered = st.text_input("Reviewer access code", type="password")
if not hmac.compare_digest(entered, access_key):
    st.info("Enter your authorised reviewer access code to inspect evidence.")
    st.stop()

st.success("Review workspace unlocked for this browser session.")
st.write(
    "Upload the team-completed CSVs below. They are parsed in memory for this "
    "review session and not written to the repository or AWS."
)
files: dict[str, bytes] = {}
cols = st.columns(2)
for idx, kind in enumerate(HEADER_GROUPS):
    with cols[idx % 2]:
        upload = st.file_uploader(
            f"{kind.title()} evidence CSV", type=["csv"],
            key=f"upload_{kind}",
            help=f"Must match columns from data/evidence_intake/{kind}.csv",
        )
        if upload is not None:
            files[kind] = upload.getvalue()
with st.expander("Ingredient-package photo evidence (manual review only)"):
    photo = st.file_uploader(
        "Photograph of ingredient packaging and printed allergen/ingredient statement",
        type=["png", "jpg", "jpeg", "webp"],
    )
    if photo is not None:
        data = photo.getvalue()
        if len(data) > 5 * 1024 * 1024:
            st.error("Image is too large; maximum 5 MB.")
        else:
            st.code(hashlib.sha256(data).hexdigest(), language=None)
            st.caption(
                "Copy this hash into the manually reviewed package record. "
                "The image is not OCR-analysed, stored or automatically approved. "
                "Verify both the ingredient list and allergen/cross-contact statement."
            )

if st.button("Validate five evidence tables", type="primary"):
    if len(files) != len(HEADER_GROUPS):
        st.error("Supply all five CSVs, even when a table contains only headers.")
    else:
        try:
            parts = {
                kind: tuple(read_evidence_csv(blob, kind))
                for kind, blob in files.items()
            }
            bundle = FieldEvidence(**parts)
            audit_evidence(bundle)
            st.success("Data shape and human-review references passed structural validation.")
            a, b, c = st.columns(3)
            a.metric("Reviewed packages", sum(r["review_status"] == "reviewed" for r in bundle.packages))
            b.metric("Reviewed sensory submissions", sum(r["review_status"] == "reviewed" for r in bundle.sensory))
            c.metric("Approved linked servings", len(bundle.approved_servings))
            st.metric(
                "Reviewed chef/restaurant feedback",
                sum(r["review_status"] == "reviewed" for r in bundle.chef_feedback),
            )
            st.caption(
                "Only actual measured servings with linked reviewed labels, "
                "batch records, and sensory observations can appear as approved."
            )
            snapshot = sensory_snapshot(bundle)
            if snapshot:
                st.dataframe(pd.DataFrame(snapshot), hide_index=True, use_container_width=True)
                st.caption(
                    "Descriptive averages for the recorded participants only. "
                    "No sensory prediction or population claim."
                )
            else:
                st.info("No reviewed consented sensory responses are present.")
            if bundle.approved_servings:
                st.dataframe(pd.DataFrame(bundle.approved_servings), hide_index=True)
        except (ValueError, TypeError, UnicodeError) as exc:
            st.error(f"Review blocked: {exc}")

with st.expander("Current committed evidence status"):
    try:
        current = load_field_evidence(INTAKE)
        st.write(
            f"Approved measured serving records committed: {len(current.approved_servings)}."
        )
        if not current.approved_servings:
            st.caption(
                "No actual approved serving-level data is present yet; "
                "Amina's sheet remains a reference, not a measured serving."
            )
    except (ValueError, OSError) as exc:
        st.error(f"Repository evidence needs review: {exc}")
