"""Pricing unit handling. Values are arithmetic fixtures, NOT current Nigerian quotes."""
import pytest

from menushift.pricing import quote_ngn_per_kg, tofu_manufacturing_cost_ngn_per_kg


def test_500g_package_and_400g_package():
    assert quote_ngn_per_kg(175, 500, "g") == 350
    assert quote_ngn_per_kg(1900, 400, "g") == 4750


def test_liquid_requires_sourced_density():
    with pytest.raises(ValueError, match="density"):
        quote_ngn_per_kg(3264, 0.75, "L")
    assert quote_ngn_per_kg(900, 1, "L", density_kg_per_litre=0.9) == 1000


def test_unsupported_pack_and_invalid_numeric_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        quote_ngn_per_kg(1900, 1, "pack")
    with pytest.raises(ValueError):
        quote_ngn_per_kg(float("nan"), 1, "kg")
    with pytest.raises(ValueError):
        quote_ngn_per_kg(1, -1, "kg")


def test_tofu_cost_requires_batch_yield_and_processing_costs():
    with pytest.raises(ValueError, match="measured_finished"):
        tofu_manufacturing_cost_ngn_per_kg(
            raw_soy_price_ngn_per_kg=644, raw_soy_used_kg=1,
            measured_finished_tofu_kg=0, coagulant_cost_ngn=5,
            energy_cost_ngn=30, labour_cost_ngn=20,
        )
    assert tofu_manufacturing_cost_ngn_per_kg(
        raw_soy_price_ngn_per_kg=600, raw_soy_used_kg=1,
        measured_finished_tofu_kg=1.5, coagulant_cost_ngn=30,
        energy_cost_ngn=150, labour_cost_ngn=120,
    ) == 600
