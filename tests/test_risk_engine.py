
import pytest

from risk_engine import classify_risk, WEIGHTS


def test_risk_categories():
    assert classify_risk(0) == "Low"
    assert classify_risk(24.99) == "Low"
    assert classify_risk(25) == "Moderate"
    assert classify_risk(49.99) == "Moderate"
    assert classify_risk(50) == "High"
    assert classify_risk(74.99) == "High"
    assert classify_risk(75) == "Critical"
    assert classify_risk(100) == "Critical"


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_weights_are_non_negative():
    assert all(weight >= 0 for weight in WEIGHTS.values())
def test_example_risk_score():
    flood_area_score = 10.0
    rainfall_score = 230.0 / 300 * 100
    population_score = 10000 / 100000 * 100
    infrastructure_score = 5 / 50 * 100

    score = (
        flood_area_score * WEIGHTS["flood_area_score"]
        + rainfall_score * WEIGHTS["rainfall_score"]
        + population_score * WEIGHTS["population_score"]
        + infrastructure_score * WEIGHTS["infrastructure_score"]
    )

    assert round(score, 2) == 26.67
    assert classify_risk(round(score, 2)) == "Moderate"