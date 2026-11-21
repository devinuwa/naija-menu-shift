"""Human-review gates for packaged ingredient labels, field batches and tasting panels.

No OCR, image model or LLM may approve food allergen safety, nutrition or taste.
The functions validate evidence completeness, not a legal or clinical certification.
All input records are provided explicitly; this module does not collect PII,
call networks, mutate GitHub or silently promote unreviewed data.
"""
from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .kitchen_optimizer import EQUIPMENT_REQUIREMENTS

INGREDIENTS = {
    "wet_awara", "fried_awara", "onion", "pepper", "salt", "seasoning", "yaji",
}
ALLERGENS = {
    "soy", "peanut", "wheat", "sesame", "milk", "egg",
    "tree nut", "fish", "shellfish", "mustard", "celery", "lupin",
}
RATINGS = ("aroma", "flavour", "texture", "appearance", "overall")
FOOD_STATE_FOR_METHOD = {
    "awara_firm": "unpressed_grilled",
    "awara_pressed": "pressed_grilled",
    "awara_frozen": "frozen_thawed_grilled",
    "awara_fried": "fried_grilled",
}


PACKAGE_HEADERS = (
    "package_id", "ingredient_id", "brand", "product_name", "batch_lot",
    "net_weight_g", "ingredient_statement", "declared_allergens",
    "may_contain_allergens", "plant_derived_review", "cross_contact_review",
    "photo_sha256", "source_reference", "reviewed_by", "review_date", "review_status",
)
BATCH_HEADERS = (
    "batch_id", "method_id", "trial_date", "purchased_awara_g",
    "finished_serving_g", "purchased_ingredient_cost_ngn", "fuel_energy_cost_ngn",
    "labour_cost_ngn", "packaging_cost_ngn", "other_cost_ngn", "prep_minutes",
    "measurement_record", "reviewed_by", "review_status",
)
SENSORY_HEADERS = (
    "trial_id", "batch_id", "method_id", "review_date", "reviewer_code",
    "consent_confirmed", "blind_code", "served_mass_g",
    "aroma", "flavour", "texture", "appearance", "overall",
    "skewer_stability", "allergen_briefing", "reviewed_by", "review_status",
)
CHEF_HEADERS = (
    "feedback_id", "batch_id", "method_id", "reviewer_code",
    "reviewer_role", "review_date", "consent_confirmed",
    "prep_practicality", "skewer_workability", "customer_fit",
    "observations", "reviewed_by", "review_status",
)
SERVING_HEADERS = (
    "serving_id", "batch_id", "method_id", "package_ids",
    "protein_g", "protein_evidence_type", "protein_source",
    "serving_food_state", "approved_by", "review_date", "review_status",
)
HEADER_GROUPS = {
    "packages": PACKAGE_HEADERS, "batches": BATCH_HEADERS,
    "sensory": SENSORY_HEADERS, "chef_feedback": CHEF_HEADERS,
    "servings": SERVING_HEADERS,
}


@dataclass(frozen=True)
class FieldEvidence:
    packages: tuple[dict[str, str], ...]
    batches: tuple[dict[str, str], ...]
    sensory: tuple[dict[str, str], ...]
    chef_feedback: tuple[dict[str, str], ...]
    servings: tuple[dict[str, str], ...]

    @property
    def approved_servings(self) -> tuple[dict[str, str], ...]:
        """Only independently reviewed and cross-linked servings; not food-safe approval."""
        audit_evidence(self)
        return tuple(row for row in self.servings if row["review_status"] == "approved")


def read_evidence_csv(
    content: bytes | str, kind: str, *, max_rows: int = 500,
) -> list[dict[str, str]]:
    """Read a bounded CSV preserving exact headers and malformed-row errors."""
    if kind not in HEADER_GROUPS:
        raise ValueError("Unknown evidence record kind")
    if isinstance(content, bytes):
        if len(content) > 1024 * 1024:
            raise ValueError("Evidence CSV exceeds 1 MB")
        decoded = content.decode("utf-8-sig")
    elif isinstance(content, str):
        if len(content) > 1024 * 1024:
            raise ValueError("Evidence CSV exceeds 1 MB")
        decoded = content.lstrip("\ufeff")
    else:
        raise TypeError("Evidence data must be UTF-8 bytes or text")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    if tuple(reader.fieldnames or ()) != HEADER_GROUPS[kind]:
        raise ValueError(f"{kind}: unexpected or missing CSV columns")
    rows = []
    for n, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{kind}: malformed CSV at line {n}")
        rows.append(row)
        if len(rows) > max_rows:
            raise ValueError("Too many evidence records")
    return rows


def _required(row: dict[str, str], *fields: str) -> None:
    for field in fields:
        if not row.get(field, "").strip():
            raise ValueError(f"{row.get('package_id') or row.get('batch_id') or row.get('serving_id') or 'record'}: {field} missing")


def _date(raw: str, field: str) -> None:
    try:
        value = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field}: invalid ISO date") from exc
    if value > date.today():
        raise ValueError(f"{field}: future date")


def _number(raw: str, field: str, *, zero: bool = True, maximum: float = 1e8) -> float:
    try:
        number = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < 0 or (not zero and number == 0) or number > maximum:
        raise ValueError(f"{field} outside valid range")
    return number


def _allergen_field(value: str, *, allow_none: bool) -> set[str]:
    labels = {part.strip().lower() for part in value.split(";") if part.strip()}
    if not labels:
        raise ValueError("Allergen declaration cannot be blank")
    if labels == {"none"} and allow_none:
        return set()
    if "none" in labels or "unknown" in labels or not labels <= ALLERGENS:
        raise ValueError("Allergen labels must use known names or explicit none where allowed")
    return labels


def validate_package(row: dict[str, str]) -> None:
    if set(row) != set(PACKAGE_HEADERS):
        raise ValueError("Package record schema mismatch")
    _required(row, "package_id", "ingredient_id", "review_status")
    if row["ingredient_id"] not in INGREDIENTS:
        raise ValueError("Unknown ingredient ID")
    status = row["review_status"]
    if status not in {"pending", "reviewed", "rejected"}:
        raise ValueError("Invalid package review status")
    if status != "reviewed":
        return
    _required(
        row, "brand", "product_name", "net_weight_g", "ingredient_statement",
        "declared_allergens", "may_contain_allergens", "photo_sha256",
        "source_reference", "reviewed_by", "review_date", "plant_derived_review",
        "cross_contact_review",
    )
    _date(row["review_date"], "package review date")
    _number(row["net_weight_g"], "net_weight_g", zero=False)
    photo = row["photo_sha256"].strip().lower()
    if len(photo) != 64 or any(c not in "0123456789abcdef" for c in photo):
        raise ValueError("Reviewed packaging needs a real SHA-256 image evidence reference")
    declared = _allergen_field(row["declared_allergens"], allow_none=True)
    _allergen_field(row["may_contain_allergens"], allow_none=True)
    if row["plant_derived_review"] not in {"yes", "no", "unknown"}:
        raise ValueError("plant_derived_review must be yes, no or unknown")
    if row["cross_contact_review"] not in {"assessed", "unknown"}:
        raise ValueError("Cross-contact assessment must be explicitly recorded")
    if row["ingredient_id"] in {"wet_awara", "fried_awara"} and "soy" not in declared:
        raise ValueError("Awara/tofu must not be represented as soy-free")
    if row["ingredient_id"] == "yaji" and row["plant_derived_review"] == "unknown":
        raise ValueError("Yaji animal-derived ingredients remain unreviewed")
    # Cross-contact status 'assessed' never means allergy-safe or no cross-contact.


def validate_batch(row: dict[str, str]) -> None:
    if set(row) != set(BATCH_HEADERS):
        raise ValueError("Batch schema mismatch")
    _required(row, "batch_id", "method_id", "trial_date", "review_status")
    if row["method_id"] not in EQUIPMENT_REQUIREMENTS:
        raise ValueError("Unknown batch method")
    _date(row["trial_date"], "batch date")
    if row["review_status"] not in {"pending", "reviewed", "rejected"}:
        raise ValueError("Unknown batch review status")
    if row["review_status"] != "reviewed":
        return
    _required(row, *BATCH_HEADERS[3:-1])
    for field in (
        "purchased_awara_g", "finished_serving_g", "purchased_ingredient_cost_ngn",
        "fuel_energy_cost_ngn", "labour_cost_ngn", "packaging_cost_ngn",
        "other_cost_ngn", "prep_minutes",
    ):
        _number(row[field], field, zero=field not in {
            "purchased_awara_g", "finished_serving_g", "prep_minutes",
        })
    _required(row, "measurement_record", "reviewed_by")
    if _number(row["finished_serving_g"], "finished_serving_g") > (
        _number(row["purchased_awara_g"], "purchased_awara_g") + 1000
    ):
        raise ValueError("Implausible serving yield; check purchased and finished food states")


def validate_sensory(row: dict[str, str]) -> None:
    if set(row) != set(SENSORY_HEADERS):
        raise ValueError("Sensory record schema mismatch")
    _required(row, "trial_id", "batch_id", "method_id", "review_status")
    if row["method_id"] not in EQUIPMENT_REQUIREMENTS:
        raise ValueError("Unknown sensory method")
    if row["review_status"] not in {"pending", "reviewed", "rejected"}:
        raise ValueError("Unknown sensory review status")
    if row["review_status"] != "reviewed":
        return
    _required(row, *SENSORY_HEADERS[3:-1])
    _date(row["review_date"], "sensory review date")
    if row["consent_confirmed"] != "yes":
        raise ValueError("Cannot review non-consented sensory feedback")
    if row["allergen_briefing"] != "confirmed":
        raise ValueError("Sensory panel allergen briefing not confirmed")
    if not 1 < len(row["reviewer_code"]) <= 40:
        raise ValueError("Use a pseudonymous reviewer code")
    _number(row["served_mass_g"], "served_mass_g", zero=False)
    for field in RATINGS:
        val = _number(row[field], field, zero=False, maximum=9)
        if val != int(val):
            raise ValueError(f"{field} must be an integer from 1 to 9")
    if row["skewer_stability"] not in {"held", "partial", "crumbled", "not_tested"}:
        raise ValueError("Unrecognised skewer stability observation")


def validate_chef_feedback(row: dict[str, str]) -> None:
    if set(row) != set(CHEF_HEADERS):
        raise ValueError("Chef feedback schema mismatch")
    _required(row, "feedback_id", "batch_id", "method_id", "review_status")
    if row["method_id"] not in EQUIPMENT_REQUIREMENTS:
        raise ValueError("Unknown chef evaluation method")
    if row["review_status"] not in {"pending", "reviewed", "rejected"}:
        raise ValueError("Unknown chef feedback review status")
    if row["review_status"] != "reviewed":
        return
    _required(row, *CHEF_HEADERS[3:-1])
    _date(row["review_date"], "chef feedback date")
    if row["consent_confirmed"] != "yes":
        raise ValueError("Chef feedback consent is required")
    if row["reviewer_role"] not in {"chef", "restaurant_owner", "food_technologist"}:
        raise ValueError("Chef reviewer role not recognised")
    for field in ("prep_practicality", "skewer_workability", "customer_fit"):
        val = _number(row[field], field, zero=False, maximum=5)
        if val != int(val):
            raise ValueError(f"{field} must be an integer from 1 to 5")


def validate_serving(row: dict[str, str]) -> None:
    if set(row) != set(SERVING_HEADERS):
        raise ValueError("Serving schema mismatch")
    _required(row, "serving_id", "batch_id", "method_id", "review_status")
    if row["method_id"] not in EQUIPMENT_REQUIREMENTS:
        raise ValueError("Unknown serving method")
    if row["review_status"] not in {"pending", "approved", "rejected"}:
        raise ValueError("Invalid serving approval status")
    if row["review_status"] != "approved":
        return
    _required(row, *SERVING_HEADERS[3:-1])
    _date(row["review_date"], "serving review date")
    _number(row["protein_g"], "protein_g", zero=False, maximum=1000)
    if row["protein_evidence_type"] not in {"lab_measured", "matched_reference"}:
        raise ValueError("Protein evidence must state laboratory assay or matched reference")
    if not row["protein_source"].startswith(("https://", "http://", "lab-report:")):
        raise ValueError("Protein source requires a retrievable reference or lab record ID")
    if row["serving_food_state"] != FOOD_STATE_FOR_METHOD[row["method_id"]]:
        raise ValueError("Serving food state must match its tested preparation method")


def audit_evidence(bundle: FieldEvidence) -> None:
    """Fail closed: no serving approved without linked reviewed records and feedback."""
    groups: tuple[tuple[str, tuple[dict[str, str], ...], Any, str], ...] = (
        ("packages", bundle.packages, validate_package, "package_id"),
        ("batches", bundle.batches, validate_batch, "batch_id"),
        ("sensory", bundle.sensory, validate_sensory, "trial_id"),
        ("chef_feedback", bundle.chef_feedback, validate_chef_feedback, "feedback_id"),
        ("servings", bundle.servings, validate_serving, "serving_id"),
    )
    for name, records, validator, identifier in groups:
        seen: set[str] = set()
        for row in records:
            validator(row)
            key = row[identifier]
            # Multiple panel scores have different trial IDs, but may share batch ID.
            if not key or key in seen:
                raise ValueError(f"{name}: duplicate or empty {identifier}")
            seen.add(key)
    packages = {r["package_id"]: r for r in bundle.packages}
    batches = {r["batch_id"]: r for r in bundle.batches}
    for row in bundle.sensory:
        if row["review_status"] != "reviewed":
            continue
        parent = batches.get(row["batch_id"])
        if parent is None or parent["method_id"] != row["method_id"]:
            raise ValueError("Sensory trial must link to matching measured batch")
    for row in bundle.chef_feedback:
        if row["review_status"] != "reviewed":
            continue
        parent = batches.get(row["batch_id"])
        if parent is None or parent["method_id"] != row["method_id"]:
            raise ValueError("Chef feedback must link to matching measured batch")
    for row in bundle.servings:
        if row["review_status"] != "approved":
            continue
        batch = batches.get(row["batch_id"])
        if batch is None or batch["review_status"] != "reviewed":
            raise ValueError("Approved serving requires a reviewed measured batch")
        if batch["method_id"] != row["method_id"]:
            raise ValueError("Serving food method disagrees with batch")
        referenced = [x.strip() for x in row["package_ids"].split(";") if x.strip()]
        if not referenced:
            raise ValueError("Serving package evidence references are required")
        if any(pid not in packages or packages[pid]["review_status"] != "reviewed" for pid in referenced):
            raise ValueError("Serving package labels must be independently reviewed")
        if any(packages[pid]["cross_contact_review"] != "assessed" for pid in referenced):
            raise ValueError("Serving cannot be approved with unreviewed cross-contact status")
        if float(row["protein_g"]) > float(batch["finished_serving_g"]):
            raise ValueError("Serving protein cannot exceed measured finished serving mass")
        kinds = {packages[pid]["ingredient_id"] for pid in referenced}
        if not kinds & {"wet_awara", "fried_awara"} or "yaji" not in kinds:
            raise ValueError("Suya serving requires reviewed awara and yaji package/recipe records")
        yaji_records = [packages[pid] for pid in referenced if packages[pid]["ingredient_id"] == "yaji"]
        if any(p["plant_derived_review"] != "yes" for p in yaji_records):
            raise ValueError("Plant-based suya requires a verified plant-derived yaji formulation")
        if not any(
            f["batch_id"] == batch["batch_id"] and f["review_status"] == "reviewed"
            and f["method_id"] == batch["method_id"]
            for f in bundle.chef_feedback
        ):
            raise ValueError("Approved serving requires reviewed chef or restaurant-owner feedback")
        if not any(
            s["batch_id"] == batch["batch_id"] and s["review_status"] == "reviewed"
            and s["method_id"] == batch["method_id"]
            for s in bundle.sensory
        ):
            raise ValueError("Approved serving requires at least one reviewed sensory record")
        # One review is enough for linkage, not enough to claim representative taste.


def load_field_evidence(folder: str | Path) -> FieldEvidence:
    """A missing or empty table stays empty; it never becomes fabricated approved data."""
    path = Path(folder)
    groups = {}
    for name in HEADER_GROUPS:
        candidate = path / f"{name}.csv"
        if not candidate.exists():
            raise ValueError(f"Missing evidence intake table {candidate.name}")
        data = read_evidence_csv(candidate.read_bytes(), name)
        groups[name] = tuple(data)
    bundle = FieldEvidence(**groups)
    audit_evidence(bundle)
    return bundle


def sensory_snapshot(bundle: FieldEvidence) -> list[dict[str, str | float | int]]:
    """Descriptive panel aggregation only; no taste prediction or population inference."""
    audit_evidence(bundle)
    rows = [r for r in bundle.sensory if r["review_status"] == "reviewed"]
    keys = sorted({(r["batch_id"], r["method_id"]) for r in rows})
    result = []
    for batch_id, method in keys:
        group = [r for r in rows if r["batch_id"] == batch_id and r["method_id"] == method]
        result.append({
            "batch_id": batch_id, "method_id": method,
            "reviewed_responses": len(group),
            **{
                f"mean_{field}": round(sum(int(r[field]) for r in group) / len(group), 2)
                for field in RATINGS
            },
        })
    return result

def serving_snapshot(bundle: FieldEvidence) -> list[dict[str, str | float]]:
    """Reviewed measured cost/portion evidence, never a certified serving recommendation."""
    audit_evidence(bundle)
    batches = {row["batch_id"]: row for row in bundle.batches}
    summary = []
    for row in bundle.approved_servings:
        batch = batches[row["batch_id"]]
        full_cost = sum(
            float(batch[field]) for field in (
                "purchased_ingredient_cost_ngn", "fuel_energy_cost_ngn",
                "labour_cost_ngn", "packaging_cost_ngn", "other_cost_ngn",
            )
        )
        summary.append({
            "serving_id": row["serving_id"],
            "method_id": row["method_id"],
            "recorded_finished_g": float(batch["finished_serving_g"]),
            "recorded_listed_cost_ngn": round(full_cost, 2),
            "recorded_prep_minutes": float(batch["prep_minutes"]),
            "protein_g": float(row["protein_g"]),
            "protein_evidence_type": row["protein_evidence_type"],
            "protein_source": row["protein_source"],
            "review_date": row["review_date"],
            "evidence_level": "team-reviewed field record, not allergen or food-safety certification",
        })
    return summary
