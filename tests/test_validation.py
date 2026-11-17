"""Lightweight contract and regression tests for grain, cohorts and trends."""
from pathlib import Path
import pandas as pd
import pytest

from src.data import load_data, validate_table, valid_repository_ages, valid_tool_ages
from src.statistics import category_counts, monthly_counts, summary_tables


@pytest.fixture(scope="module")
def data():
    return load_data(Path(__file__).resolve().parents[1])


def test_unique_grains_and_repository_sets(data):
    r, t = data.repositories, data.tools
    assert r.repo_name.is_unique
    assert not t.duplicated(["repo_name", "spec_tool"]).any()
    assert r.repo_name.nunique() == t.repo_name.nunique()
    assert len(t) > t.repo_name.nunique()  # Guard against confusing pair count with repo count.


@pytest.mark.parametrize("tool", [False, True])
def test_duplicate_keys_are_rejected(data, tool):
    df = data.tools if tool else data.repositories
    with pytest.raises(ValueError, match="Duplicate"):
        validate_table(pd.concat([df, df.iloc[[0]]], ignore_index=True), tool)


@pytest.mark.parametrize("tool", [False, True])
def test_required_columns_are_checked(data, tool):
    df = data.tools if tool else data.repositories
    with pytest.raises(ValueError, match="Missing required"):
        validate_table(df.drop(columns="repo_stars"), tool)


@pytest.mark.parametrize("tool", [False, True])
def test_age_filters_use_status_not_positive_value_or_flag(tool):
    prefix = "tool_adoption_age" if tool else "adoption_age"
    # Deliberately conflicting values: filtering must depend on the right status.
    fixture = pd.DataFrame({f"{prefix}_status": ["valid", "valid", "predates_repo_creation", "missing_date"],
        f"{prefix}_days": [0.0, 10.0, 5.0, 99.0], f"{prefix}_valid": [False, True, True, True],
        "adoption_age_status" if tool else "tool_adoption_age_status": ["missing_date"] * 4})
    selected = valid_tool_ages(fixture) if tool else valid_repository_ages(fixture)
    assert selected.index.tolist() == [0, 1]
    assert len(fixture) == 4


def test_real_age_cohorts_and_no_global_filter(data):
    r, t = data.repositories, data.tools
    vr, vt = valid_repository_ages(r), valid_tool_ages(t)
    assert len(vr) == r.adoption_age_status.eq("valid").sum()
    assert len(vt) == t.tool_adoption_age_status.eq("valid").sum()
    tables = summary_tables(data)
    assert tables["numeric_summary"].query("variable == 'repo_stars'").n_non_null.iloc[0] == len(r)
    assert category_counts(t).sum() == len(t)
    for name in ("age_by_ownership", "age_by_language", "age_by_category"):
        table = tables[name]
        assert (table.n_non_null == table.included_valid).all()
        assert (table.total_records == table.included_valid + table.excluded_predates_repo_creation + table.excluded_missing_date).all()


def test_trends_retain_dated_predating_records(data):
    r, t = data.repositories, data.tools
    assert monthly_counts(r, "first_sdd_at").repositories.sum() == r.first_sdd_at.notna().sum()
    assert monthly_counts(t, "first_tool_adoption_at", "spec_tool").sum().sum() == t.first_tool_adoption_at.notna().sum()
    predating = r.adoption_age_status.eq("predates_repo_creation")
    assert monthly_counts(r[predating], "first_sdd_at").repositories.sum() == predating.sum()


def test_invalid_age_population_is_rejected(data):
    invalid = data.repositories.copy()
    idx = invalid.index[invalid.adoption_age_status.ne("valid")][0]
    invalid.loc[idx, "adoption_age_days"] = 1
    with pytest.raises(ValueError, match="excluded rows"):
        validate_table(invalid)


def test_input_fingerprints_match_initial_inspection(data):
    assert data.audit["input_sha256"] == {
        "repo_summary.csv": "747a92f9c9d92ce01e868b303237ceb54e729ac4c7d61fb973cef635dedc39bb",
        "repo_tool_adoption.csv": "e95ff4eeb81eea20b222a516185d89d7247f3874a44aa679c45f997e73a43114"}
