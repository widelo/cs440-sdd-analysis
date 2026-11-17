"""Descriptive summaries with explicit grains, denominators and age exclusions."""
from __future__ import annotations

import pandas as pd

from .data import Dataset, STATUSES, valid_repository_ages, valid_tool_ages


def describe_numeric(df: pd.DataFrame, columns: list[str], grain: str) -> pd.DataFrame:
    """Summarize every nonmissing value; never trim statistics to plot limits."""
    rows = []
    for col in columns:
        values = df[col].dropna()
        rows.append({"grain": grain, "variable": col, "n_non_null": len(values),
            "n_missing": int(df[col].isna().sum()), "median": values.median(),
            "mean": values.mean(), "q25": values.quantile(.25),
            "q75": values.quantile(.75), "maximum": values.max()})
    return pd.DataFrame(rows)


def age_audit(df: pd.DataFrame, tool: bool = False) -> pd.DataFrame:
    """Report included and excluded records at the correct observational grain."""
    col = "tool_adoption_age_status" if tool else "adoption_age_status"
    return pd.DataFrame([{"grain": "repository-category" if tool else "repository",
        "status": s, "records": int(df[col].eq(s).sum()),
        "included_in_age_analysis": s == "valid"} for s in STATUSES])


def grouped_age_summary(df: pd.DataFrame, group: str, age: str) -> pd.DataFrame:
    """Summarize a prefiltered age cohort; labels include missing languages."""
    work = df.assign(**{group: df[group].fillna("Missing language")})
    return work.groupby(group)[age].agg(n_non_null="count", median="median", mean="mean",
        q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75), maximum="max").reset_index()


def group_age_audit(df: pd.DataFrame, group: str, tool: bool = False) -> pd.DataFrame:
    """Attach group-specific age inclusion/exclusion counts to numeric summaries."""
    prefix = "tool_adoption_age" if tool else "adoption_age"
    work = df.assign(**{group: df[group].fillna("Missing language")})
    filtered = valid_tool_ages(work) if tool else valid_repository_ages(work)
    summary = grouped_age_summary(filtered, group, f"{prefix}_days").set_index(group)
    status_counts = pd.crosstab(work[group], work[f"{prefix}_status"]).reindex(columns=STATUSES, fill_value=0)
    summary = summary.reindex(status_counts.index)
    summary["n_non_null"] = summary.n_non_null.fillna(0).astype(int)
    summary["total_records"] = status_counts.sum(axis=1)
    summary["included_valid"] = status_counts.valid
    summary["excluded_predates_repo_creation"] = status_counts.predates_repo_creation
    summary["excluded_missing_date"] = status_counts.missing_date
    return summary.reset_index()


def monthly_counts(df: pd.DataFrame, date_column: str, group: str | None = None) -> pd.DataFrame:
    """Count distinct repositories per first-detection month (and optional category).

    A repository can occur in several categories. Category counts must not be summed
    as an overall repository count. Missing dates are excluded only here.
    """
    work = df.loc[df[date_column].notna()].copy()
    if work.empty:
        return pd.DataFrame()
    work["month"] = work[date_column].dt.tz_convert(None).dt.to_period("M").dt.to_timestamp()
    months = pd.date_range(work.month.min(), work.month.max(), freq="MS")
    if group:
        return work.groupby(["month", group]).repo_name.nunique().unstack(fill_value=0).reindex(months, fill_value=0).rename_axis("month")
    return work.groupby("month").repo_name.nunique().reindex(months, fill_value=0).rename("repositories").to_frame().rename_axis("month")


def annual_counts(repos: pd.DataFrame) -> pd.DataFrame:
    """Count first-detected repositories by documented adoption_year."""
    return repos.dropna(subset=["first_sdd_at", "adoption_year"]).groupby("adoption_year").repo_name.nunique().rename("repositories").to_frame().rename_axis("year")


def category_counts(tools: pd.DataFrame) -> pd.Series:
    """Repository counts for each detected category; overlapping memberships."""
    return tools.groupby("spec_tool").repo_name.nunique().sort_values(ascending=False)


def summary_tables(data: Dataset) -> dict[str, pd.DataFrame]:
    """Build exportable numeric summaries, status audits and trend tables."""
    r, t = data.repositories, data.tools
    vr, vt = valid_repository_ages(r), valid_tool_ages(t)
    numeric = pd.concat([
        describe_numeric(r, ["repo_stars", "repo_forks", "num_specs", "num_sdd_tools",
                            "num_logged_in_spec_contributors"], "repository"),
        describe_numeric(vr, ["adoption_age_days", "adoption_age_years"], "repository: valid ages"),
        describe_numeric(t, ["num_specs_for_tool"], "repository-category"),
        describe_numeric(vt, ["tool_adoption_age_days", "tool_adoption_age_years"], "repository-category: valid ages"),
    ], ignore_index=True)
    return {"numeric_summary": numeric,
        "age_status_audit": pd.concat([age_audit(r), age_audit(t, True)], ignore_index=True),
        "age_by_ownership": group_age_audit(r, "owner_type"),
        "age_by_language": group_age_audit(r, "repo_language"),
        "age_by_category": group_age_audit(t, "spec_tool", True),
        "monthly_repository_counts": monthly_counts(r, "first_sdd_at"),
        "annual_repository_counts": annual_counts(r),
        "monthly_category_counts": monthly_counts(t, "first_tool_adoption_at", "spec_tool"),
        "monthly_repository_counts_by_age_status": monthly_counts(r, "first_sdd_at", "adoption_age_status"),
        "category_repository_counts": category_counts(t).rename("repositories").to_frame(),
        "language_counts": r.repo_language.fillna("Missing language").value_counts().rename_axis("language").rename("repositories").to_frame(),
        "ownership_counts": r.owner_type.value_counts().rename_axis("ownership").rename("repositories").to_frame()}
