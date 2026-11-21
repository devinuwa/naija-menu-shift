"""Reference integrity and read-only Streamlit evidence browser."""
import csv
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from menushift.evidence_catalog import load_nutrition_references, load_wfp_price_snapshots

ROOT = Path(__file__).resolve().parents[1]
CURATED = ROOT / "data" / "curated"


def test_source_counts_and_no_recipe_auto_approval():
    rows = load_nutrition_references()
    assert len(rows) == 15
    keys = {r["reference_id"] for r in rows}
    assert "WAFCT2019:03_004" in keys
    assert "USDA:172475" in keys
    assert "USDA:174268" in keys
    assert all(r["local_recipe_approved"] == "no" for r in rows)
    assert not any("Vchunks" in r["food_name"] for r in rows)


def test_wfp_scope_and_unit_normalization():
    rows = load_wfp_price_snapshots()
    assert len(rows) == 28
    assert {r["state"] for r in rows} == {"Borno", "Yobe"}
    assert {r["month"] for r in rows} == {"2026-10", "2026-11"}
    assert all(r["priceflag"] == "aggregate" for r in rows)
    beef = next(r for r in rows if r["month"] == "2026-11"
                and r["state"] == "Borno" and r["commodity"] == "Meat (beef)")
    assert float(beef["median_ngn_per_kg"]) == 6500
    assert all(not r["median_ngn_per_kg"] for r in rows if r["original_unit"] == "L")


def test_duplicate_schema_rejected(tmp_path):
    header = (CURATED / "nutrition_references.csv").read_text().splitlines()[0]
    (tmp_path / "nutrition_references.csv").write_text(
        header.replace("reference_id,source", "reference_id,reference_id") + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="columns"):
        load_nutrition_references(tmp_path)


def test_source_reference_cannot_claim_kitchen_approval(tmp_path):
    with (CURATED / "nutrition_references.csv").open(encoding="utf-8", newline="") as src:
        rows = list(csv.DictReader(src))
    row = dict(rows[0])
    row["local_recipe_approved"] = "yes"
    with (tmp_path / "nutrition_references.csv").open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    with pytest.raises(ValueError, match="must not claim"):
        load_nutrition_references(tmp_path)


def test_library_app_renders_without_exceptions():
    app = AppTest.from_file(str(ROOT / "pages" / "2_Evidence_Library.py"), default_timeout=30).run()
    assert not app.exception
    assert any("Evidence Library" in title.value for title in app.title)
    assert app.warning
    assert any("Food composition" in title.value for title in app.subheader)
