import pandas as pd

from core.profiler import profile_dataset
from core.scoring import calculate_quality_score, rank_column_risks
from core.readiness import assess_modelling_readiness
from core.recommendations import build_action_plan


def test_profile_dataset_detects_basic_quality_issues():
    df = pd.DataFrame(
        {
            "age": [20, 21, 22, 1000, None],
            "region": ["A", "A", "B", "B", "B"],
            "target": ["yes", "no", "no", "no", "no"],
        }
    )

    profile = profile_dataset(df)

    assert profile["rows"] == 5
    assert profile["columns"] == 3
    assert len(profile["column_profiles"]) == 3


def test_quality_score_and_risks_return_expected_shapes():
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, None],
            "y": [1, 1, 1, 1],
            "target": [0, 0, 1, 1],
        }
    )

    profile = profile_dataset(df)
    quality = calculate_quality_score(profile)
    risks = rank_column_risks(profile)

    assert "score" in quality
    assert isinstance(risks, list)
    assert len(risks) == 3


def test_modelling_readiness_for_classification_target():
    df = pd.DataFrame(
        {
            "feature": [1, 2, 3, 4, 5],
            "target": ["no", "no", "no", "no", "yes"],
        }
    )

    profile = profile_dataset(df)
    readiness = assess_modelling_readiness(df, profile, "target")

    assert readiness["available"] is True
    assert readiness["task_type"] == "Classification"


def test_action_plan_returns_at_least_one_action():
    df = pd.DataFrame(
        {
            "feature": [1, 2, None, 4],
            "target": [0, 0, 1, 1],
        }
    )

    profile = profile_dataset(df)
    quality = calculate_quality_score(profile)
    risks = rank_column_risks(profile)
    readiness = assess_modelling_readiness(df, profile, "target")
    actions = build_action_plan(profile, risks, readiness)

    assert len(actions) >= 1
