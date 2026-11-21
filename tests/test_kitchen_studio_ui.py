"""Streamlit AppTest covers functional UX but not actual mobile rendering."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

PAGE = Path(__file__).resolve().parents[1] / "pages" / "1_Kitchen_Intelligence.py"


def launch():
    app = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not app.exception
    return app


def test_kitchen_studio_renders_clear_restaurant_fields():
    app = launch()
    assert any("Which menu would you like to diversify?" in h.value for h in app.subheader)
    assert any("Maximum estimated cost" in x.label for x in app.number_input)
    assert any("Minimum estimated protein" in x.label for x in app.number_input)
    assert any("What equipment is available?" == x.label for x in app.multiselect)
    assert any("Research prototype" in x.value for x in app.warning)


def test_budget_too_low_abstains_in_ui():
    app = launch()
    item = next(x for x in app.number_input if "Maximum estimated cost" in x.label)
    item.set_value(1.0).run()
    assert not app.exception
    assert any("No plant-based formulation" in x.value for x in app.error)


def test_no_grill_blocks_all_candidates_in_ui():
    app = launch()
    item = next(x for x in app.multiselect if x.label == "What equipment is available?")
    item.set_value([]).run()
    assert not app.exception
    assert any("No plant-based formulation" in x.value for x in app.error)


def test_second_dish_studio_labels_unpriced_meal_parts():
    app = launch()
    select = next(box for box in app.selectbox if box.label == "Existing menu dish")
    select.set_value("jollof_side").run()
    assert not app.exception
    assert any("PARTIAL menu adaptation" in w.value for w in app.warning)
    assert any("Formulation" in x.value or "Find a formulation" in x.value for x in app.subheader)
