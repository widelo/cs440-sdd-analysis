"""Repository-grain visualizations for repository profiles, ages and time trends."""
from __future__ import annotations

from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import valid_repository_ages
from .plotting import BLUE, ORANGE, Chart, bar_labels, finish, log_ticks
from .statistics import annual_counts, grouped_age_summary, monthly_counts


def age_caption(repos: pd.DataFrame) -> str:
    """Always disclose included/excluded statuses for repository-age plots."""
    c = repos.adoption_age_status.value_counts()
    return (f"Age cohort: {c.get('valid', 0):,} valid repositories included; "
            f"{c.get('predates_repo_creation', 0):,} predating and {c.get('missing_date', 0):,} missing-date records excluded.")


def languages(repos: pd.DataFrame, out: Path) -> Chart:
    """Top ten known languages plus explicit missing and other-language buckets."""
    known = repos.repo_language.dropna().value_counts()
    counts = known.head(10).copy()
    counts.loc["Other known languages"] = known.iloc[10:].sum()
    counts.loc["Missing language"] = repos.repo_language.isna().sum()
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = [BLUE] * 10 + ["#777777", ORANGE]
    ax.barh(counts.index[::-1], counts.values[::-1], color=colors[::-1])
    ax.set(title="RQ1 · Main programming languages in sampled SDD repositories", xlabel="Repositories (count)")
    bar_labels(ax)
    caption = f"One row per repository; all {len(repos):,} repositories retained. Top 10 known languages; other known and missing languages shown separately."
    top = known.index[0]
    interpretation = (f"{top} is the most frequent main language ({known.iloc[0]:,} repositories; "
                      f"{known.iloc[0]/len(repos):.1%} of this sample). Language is missing for {repos.repo_language.isna().sum():,} repositories.")
    return finish(fig, "rq1_languages", out, caption, interpretation, counts.rename("repositories").to_frame())


def ownership(repos: pd.DataFrame, out: Path) -> Chart:
    counts = repos.owner_type.fillna("Missing ownership").value_counts()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(counts.index, counts.values, color=[BLUE, ORANGE, "#777777"][:len(counts)])
    ax.set(title="RQ1 · Repository ownership", ylabel="Repositories (count)", xlabel="GitHub owner type")
    bar_labels(ax, False)
    caption = f"Repository-level counts; denominator = {len(repos):,} sampled repositories, including every adoption-age status."
    interpretation = "; ".join(f"{k}: {v:,} ({v/len(repos):.1%})" for k, v in counts.items()) + ". These are sample shares."
    return finish(fig, "rq1_ownership", out, caption, interpretation, counts.rename("repositories").to_frame())


def count_distribution(repos: pd.DataFrame, out: Path, columns: list[str],
                       titles: list[str], name: str) -> Chart:
    """Histogram full distributions with log1p x coordinates and original-unit ticks."""
    fig, axes = plt.subplots(1, len(columns), figsize=(11 if len(columns) > 1 else 9, 5.8), squeeze=False)
    findings = []
    for ax, col, title in zip(axes.flat, columns, titles):
        values = repos[col].dropna()
        ax.hist(np.log1p(values), bins=45, color=BLUE, edgecolor="white", linewidth=.4)
        ax.axvline(np.log1p(values.median()), color=ORANGE, linestyle="--", label=f"Median = {values.median():,.0f}")
        log_ticks(ax, values.max())
        ax.set(title=title, xlabel="Count per repository (log1p spacing)", ylabel="Repositories (count)")
        ax.legend(fontsize=9)
        findings.append(f"{title}: median {values.median():,.0f}, mean {values.mean():,.2f}, maximum {values.max():,.0f} (n={len(values):,}).")
    caption = (f"All {len(repos):,} repository rows retained; equal-width bins in ln(1 + count), with ticks in original units. "
               "Zero values and the full tail are included; reported statistics use all nonmissing values.")
    return finish(fig, name, out, caption, " ".join(findings), repos[columns].copy())


def popularity(repos: pd.DataFrame, out: Path) -> Chart:
    return count_distribution(repos, out, ["repo_stars", "repo_forks"], ["RQ1 · Stars", "RQ1 · Forks received"], "rq1_stars_forks")


def specifications(repos: pd.DataFrame, out: Path) -> Chart:
    return count_distribution(repos, out, ["num_specs"], ["RQ1 · Detected specification files per repository"], "rq1_specifications")


def contributors(repos: pd.DataFrame, out: Path) -> Chart:
    chart = count_distribution(repos, out, ["num_logged_in_spec_contributors"],
        ["RQ1 · Logged-in specification contributors per repository"], "rq1_contributors")
    chart.interpretation += " Counts cover unique GitHub accounts committing to detected specification files, not all repository contributors; zero does not establish no human activity."
    return chart


def adoption_age_distribution(repos: pd.DataFrame, out: Path) -> Chart:
    valid = valid_repository_ages(repos)
    values = valid.adoption_age_days
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(np.log1p(values), bins=55, color=BLUE, edgecolor="white", linewidth=.4)
    ax.axvline(np.log1p(values.median()), color=ORANGE, linestyle="--", label=f"Median = {values.median():,.2f} days")
    log_ticks(ax, values.max(), ages=True)
    ax.set(title="RQ2 · Repository age at first detected SDD use", xlabel="Age (days; log1p spacing)", ylabel="Valid repositories (count)")
    ax.legend()
    caption = age_caption(repos) + " Equal-width ln(1 + days) bins; original-day ticks. Zero and the full tail retained."
    interpretation = (f"Among valid ages, the median is {values.median():,.2f} days and the middle 50% spans "
        f"{values.quantile(.25):,.2f}–{values.quantile(.75):,.2f} days. The mean is {values.mean():,.2f} days; "
        f"{values.le(1).mean():.1%} of valid records have rounded ages of at most one day. This is conditional on valid chronology.")
    return finish(fig, "rq2_repository_age", out, caption, interpretation, valid[["repo_name", "adoption_age_days"]])


def age_groups(repos: pd.DataFrame, out: Path, group: str = "owner_type") -> Chart:
    """Show medians and interquartile ranges; common languages chosen on full sample."""
    valid = valid_repository_ages(repos)
    summary = grouped_age_summary(valid, group, "adoption_age_days").set_index(group)
    excluded = 0
    if group == "repo_language":
        chosen = repos.repo_language.dropna().value_counts().head(10).index
        summary = summary.reindex(chosen).dropna(subset="median")
        excluded = len(valid) - int(summary.n_non_null.sum())
    summary = summary.sort_values("median")
    fig, ax = plt.subplots(figsize=(10, 6.8 if group == "repo_language" else 5.5))
    y = np.arange(len(summary))
    ax.hlines(y, np.log1p(summary.q25), np.log1p(summary.q75), color=BLUE, linewidth=3)
    ax.scatter(np.log1p(summary["median"]), y, color=ORANGE, marker="D", zorder=3, label="Median; line = 25th–75th percentiles")
    ax.set_yticks(y, [f"{k}  (n={int(row.n_non_null):,})" for k, row in summary.iterrows()])
    log_ticks(ax, summary.q75.max(), ages=True)
    ax.set(xlabel="Valid adoption age (days; log1p spacing)", ylabel="Main language" if group == "repo_language" else "Owner type",
           title="RQ2 · Adoption ages by " + ("common main language" if group == "repo_language" else "ownership"))
    ax.legend(loc="lower right", fontsize=8)
    caption = age_caption(repos) + " Diamonds = medians; lines = IQRs, not confidence intervals."
    if group == "repo_language":
        caption += f" Top 10 known languages chosen from all repositories; {excluded:,} other/missing-language valid records are outside this display."
    interpretation = "; ".join(f"{k}: median {row['median']:,.2f} days (valid n={int(row.n_non_null):,})" for k, row in summary.iterrows()) + ". Differences are descriptive and do not establish causation."
    return finish(fig, "rq2_age_by_" + ("language" if group == "repo_language" else "ownership"), out, caption, interpretation, summary)


def monthly_adoption(repos: pd.DataFrame, out: Path) -> Chart:
    counts = monthly_counts(repos, "first_sdd_at")
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(counts.index, counts.repositories, color=BLUE, marker="o", markersize=4)
    last = counts.index[-1]
    ax.axvspan(last, last + pd.offsets.MonthBegin(), color=ORANGE, alpha=.15, label="July 2026: partial final month")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=35)
    ax.set(title="RQ3 · Monthly first detected SDD use", xlabel="Month of first detected SDD commit (UTC)", ylabel="Distinct repositories (count)")
    ax.legend(fontsize=9)
    caption = (f"{repos.first_sdd_at.notna().sum():,} dated repository rows; {repos.first_sdd_at.isna().sum():,} missing dates excluded. "
        f"Predating records retained. Observed dates: {repos.first_sdd_at.min():%Y-%m-%d}–{repos.first_sdd_at.max():%Y-%m-%d}. July 2026 is partial; counts are not GitHub-wide adoption rates.")
    complete = counts.iloc[:-1]
    peak = complete.repositories.idxmax()
    interpretation = f"The largest count before the partial final month is {int(complete.loc[peak, 'repositories']):,} in {peak:%B %Y}. A lower partial-month count cannot establish a decline in adoption."
    return finish(fig, "rq3_monthly_repositories", out, caption, interpretation, counts)


def annual_adoption(repos: pd.DataFrame, out: Path) -> Chart:
    counts = annual_counts(repos)
    fig, ax = plt.subplots(figsize=(9, 5.8))
    labels = [f"{int(y)}\n(partial: Jan–Jul)" if int(y) == 2026 else str(int(y)) for y in counts.index]
    ax.bar(labels, counts.repositories, color=[ORANGE if int(y) == 2026 else BLUE for y in counts.index])
    ax.set(title="RQ3 · Annual first detected SDD use", xlabel="First-detection year (2026 is incomplete)", ylabel="Distinct repositories (count)")
    bar_labels(ax, False)
    caption = (f"Calendar-year sample counts; missing first-detection dates excluded ({repos.first_sdd_at.isna().sum():,}). "
        "Predating records retained. Data end July 2026 (latest detected commit July 11); 2026 is not annualized. Sample coverage and detection can change over time.")
    interpretation = "; ".join(f"{int(y)}: {int(n):,}" for y, n in counts.repositories.items()) + ". The incomplete 2026 count is not directly comparable to a full calendar year; no GitHub-wide denominator is available."
    return finish(fig, "rq3_annual_repositories", out, caption, interpretation, counts)
