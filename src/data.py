"""Load original CSVs without rewriting them and validate their documented contracts."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

STATUSES = ("valid", "predates_repo_creation", "missing_date")
COMMON = ("repo_name", "repo_language", "owner_type", "repo_stars", "repo_forks",
          "repo_fork", "repo_created_at", "adoption_year")
REPO_COLUMNS = COMMON + ("first_sdd_at", "num_specs", "num_sdd_tools", "sdd_tools",
    "num_logged_in_spec_contributors", "adoption_age_raw_days", "adoption_age_status",
    "adoption_age_valid", "adoption_age_days", "adoption_age_years")
TOOL_COLUMNS = COMMON + ("spec_tool", "first_tool_adoption_at", "num_specs_for_tool",
    "tool_adoption_age_status", "tool_adoption_age_valid", "tool_adoption_age_days",
    "tool_adoption_age_years")
COUNT_COLUMNS = ("repo_stars", "repo_forks", "num_specs", "num_sdd_tools",
                 "num_logged_in_spec_contributors", "num_specs_for_tool")


@dataclass
class Dataset:
    """Both grains of the dataset and their validation audit."""
    repositories: pd.DataFrame
    tools: pd.DataFrame
    audit: dict[str, Any]


def require(condition: bool, message: str) -> None:
    """Raise a meaningful error even when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)


def _read(path: Path, columns: tuple[str, ...], tool: bool) -> pd.DataFrame:
    # Keep literal language labels such as 'NA'; only empty CSV fields are missing.
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])
    require(set(columns) <= set(df), f"{path.name}: missing columns {set(columns) - set(df)}")
    prefix = "tool_adoption_age" if tool else "adoption_age"
    for col in (*COUNT_COLUMNS, "adoption_year", f"{prefix}_days", f"{prefix}_years",
                "adoption_age_raw_days"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="raise")
            require(np.isfinite(df[col].dropna()).all(), f"{col}: nonfinite values")
    for col in ("repo_created_at", "first_tool_adoption_at" if tool else "first_sdd_at"):
        df[col] = pd.to_datetime(df[col], utc=True, errors="raise")
    for col in ("repo_fork", f"{prefix}_valid"):
        mapped = df[col].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})
        require(mapped.notna().all(), f"{col}: invalid boolean")
        df[col] = mapped.astype(bool)
    return df


def validate_table(df: pd.DataFrame, tool: bool = False) -> dict[str, Any]:
    """Check grain, counts, timestamps, age status, flags and cleaned ages."""
    expected = TOOL_COLUMNS if tool else REPO_COLUMNS
    require(set(expected) <= set(df), f"Missing required columns: {set(expected) - set(df)}")
    key = ["repo_name", "spec_tool"] if tool else ["repo_name"]
    require(df[key].notna().all().all(), f"Missing key: {key}")
    require(not df.duplicated(key).any(), f"Duplicate rows at grain {key}")
    require(df.repo_name.str.match(r"^[^/\s]+/[^/\s]+$").all(), "Invalid repository name")
    for col in COUNT_COLUMNS:
        if col in df:
            require(df[col].notna().all() and df[col].ge(0).all()
                    and df[col].mod(1).eq(0).all(), f"{col}: expected nonnegative integer counts")
    prefix = "tool_adoption_age" if tool else "adoption_age"
    status = df[f"{prefix}_status"]
    require(status.isin(STATUSES).all(), f"Unknown {prefix} status")
    valid = status.eq("valid")
    date = df["first_tool_adoption_at" if tool else "first_sdd_at"]
    missing = date.isna() | df.repo_created_at.isna()
    require(status.eq("missing_date").equals(missing), f"{prefix}: missing-date status mismatch")
    chronology_valid = (~missing) & date.ge(df.repo_created_at)
    require(valid.equals(chronology_valid), f"{prefix}: timestamp/status mismatch")
    require(df[f"{prefix}_valid"].eq(valid).all(), f"{prefix}: validity flag mismatch")
    for unit in ("days", "years"):
        age = df[f"{prefix}_{unit}"]
        require(age[valid].notna().all() and age[valid].ge(0).all(), f"{prefix}: invalid clean {unit}")
        require(age[~valid].isna().all(), f"{prefix}: excluded rows contain clean ages")
    raw_days = (date - df.repo_created_at).dt.total_seconds() / 86400
    require(np.allclose(df.loc[valid, f"{prefix}_days"], raw_days[valid], atol=.011, rtol=0),
            f"{prefix}: clean days disagree with timestamps")
    # The data dictionary specifies years converted from days, without a divisor.
    # Accommodate 365 or 365.25 and rounding; days are the analysis unit.
    require(np.allclose(df.loc[valid, f"{prefix}_years"],
                        df.loc[valid, f"{prefix}_days"] / 365.25, atol=.011, rtol=.001),
            f"{prefix}: years inconsistent with days")
    if not tool:
        require(np.allclose(df.adoption_age_raw_days, raw_days, atol=.011, rtol=0, equal_nan=True),
                "Raw repository age disagrees with timestamps")
    require(df.adoption_year.isna().equals(date.isna()), "Adoption year missingness mismatch")
    require(df.loc[date.notna(), "adoption_year"].eq(date.dropna().dt.year).all(), "Adoption year mismatch")
    return {"rows": len(df), "unique_repositories": df.repo_name.nunique(),
            "age_status_counts": {s: int(status.eq(s).sum()) for s in STATUSES},
            "date_min": str(date.min()), "date_max": str(date.max()),
            "missing_language": int(df.repo_language.isna().sum()),
            "missing_adoption_date": int(date.isna().sum()),
            "fork_flag_counts": {str(k): int(v) for k, v in df.repo_fork.value_counts().items()},
            "missing_by_column": {c: int(n) for c, n in df.isna().sum().items()}}


def validate_cross_tables(repos: pd.DataFrame, tools: pd.DataFrame) -> None:
    """Confirm common metadata and repository/category aggregates agree."""
    require(set(repos.repo_name) == set(tools.repo_name), "Repository sets differ")
    indexed = repos.set_index("repo_name")
    aggregates = tools.groupby("repo_name").agg(
        category_count=("spec_tool", "size"), spec_count=("num_specs_for_tool", "sum"),
        first_date=("first_tool_adoption_at", "min"))
    indexed = indexed.loc[aggregates.index]
    require(indexed.num_sdd_tools.eq(aggregates.category_count).all(), "Category count mismatch")
    require(indexed.num_specs.eq(aggregates.spec_count).all(), "Specification total mismatch")
    same_dates = indexed.first_sdd_at.eq(aggregates.first_date) | (
        indexed.first_sdd_at.isna() & aggregates.first_date.isna())
    require(same_dates.all(), "First repository/category adoption dates differ")
    category_sets = tools.groupby("repo_name").spec_tool.agg(set)
    require(all({s.strip() for s in str(indexed.loc[k, "sdd_tools"]).split(",")} == v
                for k, v in category_sets.items()), "Category list differs from category rows")
    joined = tools.merge(repos[list(COMMON)].drop(columns="adoption_year"), on="repo_name",
                         validate="many_to_one", suffixes=("_tool", "_repo"))
    for col in set(COMMON) - {"repo_name", "adoption_year"}:
        a, b = joined[f"{col}_tool"], joined[f"{col}_repo"]
        require((a.eq(b) | (a.isna() & b.isna())).all(), f"Cross-table {col} mismatch")


def load_data(root: Path | str = ".") -> Dataset:
    """Load and strictly validate the original files; never modify either input."""
    root = Path(root)
    repo_path, tool_path = root / "data/repo_summary.csv", root / "data/repo_tool_adoption.csv"
    repos = _read(repo_path, REPO_COLUMNS, False)
    tools = _read(tool_path, TOOL_COLUMNS, True)
    audit = {"repositories": validate_table(repos), "tools": validate_table(tools, True)}
    validate_cross_tables(repos, tools)
    audit["cross_table_checks"] = "passed"
    audit["input_sha256"] = {p.name: sha256(p.read_bytes()).hexdigest() for p in (repo_path, tool_path)}
    audit["data_dictionary_read"] = (root / "DATA_COLUMNS.md").exists()
    if (root / "DATA_COLUMNS.md").exists():
        audit["data_dictionary_sha256"] = sha256((root / "DATA_COLUMNS.md").read_bytes()).hexdigest()
    audit["observation_note"] = "Dataset ends July 2026; last detected date is not a verified extraction timestamp."
    return Dataset(repos, tools, audit)


def valid_repository_ages(repos: pd.DataFrame) -> pd.DataFrame:
    """Select repository ages using only the documented repository status."""
    return repos.loc[repos.adoption_age_status.eq("valid")].copy()


def valid_tool_ages(tools: pd.DataFrame) -> pd.DataFrame:
    """Select category ages using only the documented category-specific status."""
    return tools.loc[tools.tool_adoption_age_status.eq("valid")].copy()
