"""Functional-properties module: coverage, citations and honesty labels."""
import pytest

from menushift.functional import (
    LEVELS,
    PROTEIN_FUNCTIONS,
    functional_summary,
    get_protein_function,
    plant_proteins,
)

REQUIRED_PLANT_IDS = {"soy_chunks", "awara", "soy_milk", "egusi", "bambara", "mushrooms", "dawadawa", "seitan"}


def test_seitan_is_gluten_and_labelled_as_such():
    entry = get_protein_function("seitan")
    assert entry.protein_g_per_100g == 25.0
    assert "gluten" in entry.kitchen_meaning.lower()
FOUR_PROPERTIES = ("solubility", "water_holding", "emulsification", "gelation")


def test_every_catalogue_protein_has_all_four_properties():
    for entry in PROTEIN_FUNCTIONS:
        for prop in FOUR_PROPERTIES:
            assert getattr(entry.functional, prop) in LEVELS, (entry.id, prop)


def test_plant_catalogue_covers_the_core_swap_proteins():
    ids = {e.id for e in plant_proteins()}
    assert REQUIRED_PLANT_IDS <= ids


def test_animal_references_are_never_plant_options():
    for entry in plant_proteins():
        assert not entry.is_animal_reference
    for ref_id in ("beef", "chicken"):
        assert get_protein_function(ref_id).is_animal_reference


def test_protein_values_carry_dataset_citations():
    for entry in PROTEIN_FUNCTIONS:
        assert entry.protein_g_per_100g > 0
        assert entry.nutrition_source  # every figure names its dataset row


def test_wafct_spot_values_match_the_verified_pack():
    # Triple-checked against FAO/INFOODS WAFCT 2019 in the datasets pack.
    assert get_protein_function("dawadawa").protein_g_per_100g == 33.1
    assert get_protein_function("egusi").protein_g_per_100g == 19.5
    assert get_protein_function("bambara").protein_g_per_100g == 19.5
    assert get_protein_function("chicken").protein_g_per_100g == 23.0
    assert get_protein_function("beef").protein_g_per_100g == 20.3


def test_mushrooms_are_never_a_protein_source():
    # 3.09 g/100 g: flavour/texture only - the module must not oversell them.
    assert get_protein_function("mushrooms").protein_g_per_100g < 5


def test_unknown_protein_fails_loudly():
    with pytest.raises(ValueError):
        get_protein_function("quinoa")


def test_summary_names_all_four_properties():
    summary = functional_summary("awara")
    for label in ("Gelation", "Water-holding", "Emulsification", "Solubility"):
        assert label in summary
    assert "High" in summary  # awara gelation
