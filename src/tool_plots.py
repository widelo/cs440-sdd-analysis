"""Category-level analysis; categories overlap and are not all software products."""
from __future__ import annotations

from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .data import valid_tool_ages
from .plotting import BLUE, ORANGE, PALETTE, Chart, bar_labels, finish, log_ticks
from .statistics import category_counts, grouped_age_summary, monthly_counts


def common_categories(tools: pd.DataFrame, out: Path) -> Chart:
    counts = category_counts(tools)
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.barh(counts.index[::-1], counts.values[::-1], color=BLUE)
    ax.set(title="RQ3 · Detected SDD tool categories", xlabel="Distinct repositories per category (count)", ylabel="Dataset category label")
    bar_labels(ax)
    n = tools.repo_name.nunique()
    caption = (f"All {len(tools):,} repository-category rows across {n:,} distinct repositories retained. "
        "Membership overlaps: counts cannot be summed as unique repositories. Labels include generic/file-location categories, not only named software products.")
    interpretation = f"The leading category is {counts.index[0]} ({counts.iloc[0]:,} repositories). There are {len(counts)} category labels. root_bare and docs_embedded describe detection categories and must not be described as software products."
    return finish(fig, "rq3_categories", out, caption, interpretation, counts.rename("repositories").to_frame())


def monthly_categories(tools: pd.DataFrame, out: Path, top_n: int = 5) -> Chart:
    leaders = category_counts(tools).head(top_n).index
    counts = monthly_counts(tools, "first_tool_adoption_at", "spec_tool")[leaders]
    fig, ax = plt.subplots(figsize=(11, 6.8))
    for category, color, marker in zip(leaders, PALETTE, ["o", "s", "^", "D", "v", "P"]):
        ax.plot(counts.index, counts[category], label=category, color=color, marker=marker, markersize=3)
    last = counts.index[-1]
    ax.axvspan(last, last + pd.offsets.MonthBegin(), color=ORANGE, alpha=.12)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=35)
    ax.set(title="RQ3 · Monthly first detected use of leading SDD categories", xlabel="Category first-detection month (UTC; July 2026 partial)", ylabel="Distinct repositories per category (count)")
    ax.legend(title="Category", fontsize=9, ncol=2)
    missing = tools.first_tool_adoption_at.isna().sum()
    caption = (f"Top {top_n} categories selected by all-time distinct repository count. Category-specific dates, not repository-first dates. "
        f"{missing:,} missing-date repository-category rows excluded from trends; predating records retained. Membership overlaps; final month is partial.")
    dated = tools[tools.first_tool_adoption_at.notna()]
    interpretation = f"The leading categories are {', '.join(leaders)}. The trend table contains {len(dated):,} dated repository-category records across all categories; a repository may contribute at different months for different categories. These are first detections, not monthly active usage."
    return finish(fig, "rq3_monthly_categories", out, caption, interpretation, counts)


def categories_by_language(repos: pd.DataFrame, tools: pd.DataFrame, out: Path) -> Chart:
    """Within-language category presence uses all repositories of each language."""
    languages = repos.repo_language.dropna().value_counts().head(10).index
    categories = category_counts(tools).head(6).index
    counts = tools[tools.repo_language.isin(languages)].groupby(["repo_language", "spec_tool"]).repo_name.nunique().unstack(fill_value=0).reindex(index=languages, columns=categories, fill_value=0)
    denominators = repos.groupby("repo_language").repo_name.nunique().reindex(languages)
    percentages = counts.div(denominators, axis=0) * 100
    fig, ax = plt.subplots(figsize=(11, 7.5))
    sns.heatmap(percentages, annot=True, fmt=".1f", cmap="Blues", vmin=0, vmax=100,
        linewidths=.5, cbar_kws={"label": "Repositories in language with category (%)"}, ax=ax)
    ax.set_yticklabels([f"{lang} (N={denominators[lang]:,})" for lang in languages], rotation=0)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right")
    ax.set(title="RQ3 · Leading category presence within main languages", xlabel="Dataset SDD category", ylabel="Main language and full-sample denominator")
    caption = (f"Top 10 known languages and top 6 categories chosen on full sample. Each cell divides distinct category repositories by all repositories of that language. "
        f"Missing-language repositories ({repos.repo_language.isna().sum():,}) are outside this display. Categories overlap; row percentages need not sum to 100%.")
    max_row, max_col = percentages.stack().idxmax()
    interpretation = f"The largest displayed within-language presence is {max_col} in {max_row} ({percentages.loc[max_row, max_col]:.1f}%). These conditional sample shares do not measure adoption rates among all GitHub repositories of a language."
    table = counts.stack().rename("repositories_with_category").to_frame()
    table["language_repositories"] = [denominators[lang] for lang, _ in table.index]
    table["within_language_percent"] = percentages.stack()
    return finish(fig, "rq3_categories_by_language", out, caption, interpretation, table)


def category_ages(tools: pd.DataFrame, out: Path) -> Chart:
    """Optional category-age comparison using only category-specific valid rows."""
    valid = valid_tool_ages(tools)
    leaders = category_counts(tools).head(8).index
    summary = grouped_age_summary(valid, "spec_tool", "tool_adoption_age_days").set_index("spec_tool").reindex(leaders).dropna(subset="median").sort_values("median")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    y = np.arange(len(summary))
    ax.hlines(y, np.log1p(summary.q25), np.log1p(summary.q75), color=BLUE, linewidth=3)
    ax.scatter(np.log1p(summary["median"]), y, color=ORANGE, marker="D", zorder=3)
    ax.set_yticks(y, [f"{k} (valid n={int(r.n_non_null):,})" for k, r in summary.iterrows()])
    log_ticks(ax, summary.q75.max(), ages=True)
    ax.set(title="RQ2 · Repository age at first detected category use", xlabel="Category adoption age (days; log1p spacing)", ylabel="SDD category")
    c = tools.tool_adoption_age_status.value_counts()
    outside = len(valid) - int(summary.n_non_null.sum())
    caption = (f"Category age cohort: {len(valid):,} valid pairs included; {c.get('predates_repo_creation', 0):,} predating and "
        f"{c.get('missing_date', 0):,} missing-date pairs excluded. Top 8 categories chosen using all rows; {outside:,} valid pairs outside display. Diamonds = medians, lines = IQRs (not confidence intervals).")
    interpretation = "Category ages use tool_adoption_age_status, independently of repository-age status. Repositories may appear in multiple groups. " + "; ".join(f"{k}: {r['median']:,.2f} days" for k, r in summary.iterrows()) + "."
    return finish(fig, "rq2_category_ages", out, caption, interpretation, summary)
