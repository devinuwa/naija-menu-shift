import copy
from pathlib import Path

import pytest

from menushift.engine import Dataset, baselines, evaluate, load_dataset, sensitivity, validate_dataset

ROOT = Path(__file__).resolve().parents[1]

def test_demo_loads_and_suya_has_four_plant_options_plus_beef(demo):
    results = evaluate(demo, 'suya', budget_ngn=2000, protein_target_g=5)
    assert len(results) == 5
    assert sum(x.plant_only for x in results) == 4
    assert sum(not x.plant_only for x in results) == 1

def test_beef_never_is_recommended(demo):
    results = evaluate(demo, 'suya', budget_ngn=100000, protein_target_g=0)
    assert all(not x.feasible for x in results if x.group == 'reference')
    assert baselines(results)['recommended'] != 'beef_suya'

def test_no_option_fabricated_when_constraints_impossible(demo):
    result = evaluate(demo, 'suya', budget_ngn=1, protein_target_g=100)
    assert baselines(result)['no_feasible_option']
    assert all(x.score is None for x in result)

def test_cost_increases_by_only_ingredient_purchase_under_shock(demo):
    baseline = {r.option_id:r for r in evaluate(demo, 'suya', budget_ngn=10000, protein_target_g=0)}
    increase = {r.option_id:r for r in evaluate(demo, 'suya', budget_ngn=10000, protein_target_g=0, price_shock=0.2)}
    assert all(increase[k].cost_ngn > v.cost_ngn for k,v in baseline.items())
    assert all(increase[k].protein_g == v.protein_g for k,v in baseline.items())

def test_sensitivity_three_scenarios(demo):
    results = sensitivity(demo, 'suya', budget_ngn=2000, protein_target_g=10)
    assert set(results)=={'−20% prices','Base prices','+20% prices'}
    assert all(len(x)==5 for x in results.values())

def test_all_sources_visible_in_outputs(demo):
    results = evaluate(demo, 'suya', budget_ngn=1500, protein_target_g=1)
    assert all(r.sources for r in results)
    assert all(r.demo for r in results)

def test_no_cross_dish_hardcoding(demo):
    altered=Dataset(ingredients=demo.ingredients, dishes=demo.dishes,
                    options=[dict(row, dish_id='meat_pie') for row in demo.options],
                    items=demo.items, demo=True)
    validate_dataset(altered)
    assert len(evaluate(altered, 'meat_pie', budget_ngn=1500, protein_target_g=1))==5

def test_reject_animal_ingredient_in_plant_option(demo):
    bad_items=copy.deepcopy(demo.items)
    bad_items[0]['ingredient_id']='beef'
    bad=Dataset(demo.ingredients, demo.dishes, demo.options, bad_items, demo=True)
    with pytest.raises(ValueError, match='animal-derived'):
        validate_dataset(bad)

def test_missing_sources_fail_closed(demo):
    bad_ing=copy.deepcopy(demo.ingredients)
    bad_ing[0]['price_source']=''
    with pytest.raises(ValueError, match='price_source'):
        validate_dataset(Dataset(bad_ing, demo.dishes, demo.options, demo.items, demo=True))

def test_synthetic_rejected_in_verified_mode(demo):
    with pytest.raises(ValueError, match='synthetic'):
        validate_dataset(Dataset(demo.ingredients,demo.dishes,demo.options,demo.items,demo=False))

def test_verified_empty_templates_stop_instead_of_synthetic_fallback():
    with pytest.raises(ValueError, match='incomplete'):
        load_dataset(ROOT/'data'/'verified',demo=False)

def test_invalid_numbers_fail(demo):
    with pytest.raises(ValueError):
        evaluate(demo,'suya',budget_ngn=-1,protein_target_g=1)
    with pytest.raises(ValueError):
        evaluate(demo,'suya',budget_ngn=1500,protein_target_g=1,price_shock=-1)

def test_retrieval_preference_has_effect_when_feasible(demo):
    a=evaluate(demo,'suya',budget_ngn=5000,protein_target_g=1,preference='crispy fried')
    b=evaluate(demo,'suya',budget_ngn=5000,protein_target_g=1,preference='chewy frozen')
    scores_a={r.option_id:r.score for r in a}
    scores_b={r.option_id:r.score for r in b}
    assert scores_a['tofu_fried'] != scores_b['tofu_fried']

def test_dish_requires_options_for_recommendations(demo):
    assert evaluate(demo,'egusi',budget_ngn=1500,protein_target_g=10)==[]


def test_negative_infinite_and_nan_inputs_fail(demo):
    for value in (float('nan'), float('inf'), -float('inf')):
        with pytest.raises(ValueError, match='finite'):
            evaluate(demo, 'suya', budget_ngn=value, protein_target_g=2)


def test_invalid_nonfinite_nutrient_source_rows_rejected(demo):
    bad = copy.deepcopy(demo.ingredients)
    bad[0]['protein_g_per_100g'] = 'NaN'
    with pytest.raises(ValueError, match='finite'):
        validate_dataset(Dataset(bad, demo.dishes, demo.options, demo.items, True))


def test_duplicate_recipe_ingredient_is_rejected(demo):
    items = demo.items + [dict(demo.items[0])]
    with pytest.raises(ValueError, match='Duplicate'):
        validate_dataset(Dataset(demo.ingredients, demo.dishes, demo.options, items, True))


def test_declared_soy_allergen_exclusion_blocks_tofu(demo):
    outputs = evaluate(demo, 'suya', budget_ngn=100000, protein_target_g=0,
                       avoid_allergens=['soy'])
    assert all(not r.feasible for r in outputs if r.plant_only)
    assert all(any('allergen' in reason.lower() for reason in r.reasons) for r in outputs if r.plant_only)


def test_cost_breakdown_is_consistent(demo):
    results = evaluate(demo, 'suya', budget_ngn=100000, protein_target_g=0)
    for r in results:
        assert abs(r.cost_ngn - r.ingredient_cost_ngn - r.processing_cost_ngn) < 0.011


def test_eligible_options_report_explainable_components(demo):
    options = evaluate(demo, 'suya', budget_ngn=100000, protein_target_g=0)
    for r in options:
        assert bool(r.score_breakdown) == r.feasible
        if r.feasible:
            assert abs(sum(v for _, v in r.score_breakdown) - r.score) < 0.0001


def test_audit_synthetic_data_and_stale_prices(demo):
    from datetime import date

    from menushift.quality import audit_dataset
    records = audit_dataset(demo, as_of=date(2027, 1, 1))
    codes = {r.code for r in records}
    assert {'DEMO_ONLY', 'SYNTHETIC_INPUT', 'STALE_PRICE', 'SENSORY_UNTESTED'} <= codes


def test_overlong_preference_rejected(demo):
    with pytest.raises(ValueError, match='200'):
        evaluate(demo, 'suya', budget_ngn=100000, protein_target_g=0, preference='x'*201)
