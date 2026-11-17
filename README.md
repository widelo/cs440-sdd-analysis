# CSU CS 440: SpecMine SDD exploratory analysis

Reproducible analysis of detected spec-driven development in **73,031 GitHub repositories**, organized around:

1. **RQ1:** What types of repositories use detected SDD?
2. **RQ2:** At what repository age is SDD first detected?
3. **RQ3:** How have first detections and SDD category use changed over time?

First detected specification commits are a proxy for adoption. This sample cannot establish overall GitHub adoption rates or causation. Data end in **July 2026**, so July and 2026 are partial periods.

## Setup

Use standard CPython 3.12 (the analysis was tested on Windows). From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux, use `python3.12 -m venv .venv` and `.venv/bin/python` in place of the Windows interpreter below. `requirements.txt` pins direct dependencies; `requirements-lock.txt` records the complete tested environment on Windows, including platform-specific dependencies. Use the direct requirements for another operating system.

## Execute and validate

```powershell
.\.venv-win\Scripts\python.exe -m pytest -q
.\.venv-win\Scripts\python.exe -m src.pipeline
.\.venv-win\Scripts\python.exe scripts/execute_notebook.py
.\.venv-win\Scripts\python.exe scripts/check_outputs.py
```

The pipeline validates both inputs **before** computing analyses, then saves 14 figures at 300 DPI, numeric and cohort summaries, figure source tables/captions, validation fingerprints and a data-derived findings report. It uses Matplotlib's `Agg` backend, so no display is required. All outputs are deterministic for a fixed input/environment; PNG metadata or notebook execution timings can differ. No randomness or online data is used.

`execute_notebook.py` runs the existing notebook from top to bottom with the same Python interpreter, stops on any error, validates notebook structure and saves the executed notebook with embedded outputs. It creates an ignored workspace-local kernel specification under `.runtime/`, avoiding dependence on a global kernel installation. A local Jupyter kernel requires permission to launch a process and bind localhost ports. No remote service is used. `check_outputs.py` verifies the figure inventory, resolution, notebook execution/image outputs and original input fingerprints.

To open the notebook interactively:

```powershell
.\.venv-win\Scripts\python.exe -m jupyterlab notebooks/sdd_analysis.ipynb
```

Select the environment's Python kernel. The notebook locates the project root from either the root or `notebooks/` directory. It prints `DATA_COLUMNS.md`, validates both tables, recomputes summaries and regenerates figures, with captions and dynamic Markdown interpretations below each visualization.

To regenerate the notebook's source structure after editing its generator:

```powershell
.\.venv-win\Scripts\python.exe scripts/build_notebook.py
.\.venv-win\Scripts\python.exe scripts/execute_notebook.py
```

Building replaces the notebook source and clears saved outputs; execution restores outputs. Normal analysis does not require rebuilding.

## Data rules

Read [DATA_COLUMNS.md](DATA_COLUMNS.md) for all definitions and [DATA_VALIDATION.md](DATA_VALIDATION.md) for the implemented checks.

- `data/repo_summary.csv`: one row per unique repository; source for repository counts and profile summaries.
- `data/repo_tool_adoption.csv`: one row per repository-category pair; use distinct `repo_name` for repository counts. Category memberships overlap. `spec_tool` includes generic/location labels such as `root_bare` and `docs_embedded`, not just named products.
- Repository ages require `adoption_age_status == "valid"`. Category ages independently require `tool_adoption_age_status == "valid"`. Neither filter is applied globally. Zero-day valid ages are retained.
- Other statuses remain in profiles, popularity and category counts; time trends include dated predating histories and exclude missing first-detection dates only. Repository and category trends use their own first-detection dates.
- `repo_fork` is uniformly False/0: no fork-vs-non-fork comparison. `repo_forks` is the number of forks received and is analyzed numerically.
- Full-tail statistics report non-null count, missing count, median, mean, quartiles and maximum. Heavy-skew plots use log1p spacing with original-unit ticks, retaining zeros and outliers. Group age tables include per-status inclusion/exclusion counts. IQRs are descriptive, not confidence intervals.
- Input CSVs are read only. Tests check SHA-256 fingerprints captured before implementation. Updating the source dataset deliberately requires reviewing and updating that regression test.

## Layout

| File/directory | Purpose |
| --- | --- |
| `src/data.py` | Loading, documented schema/grain checks, timestamps, status rules, cross-table agreement |
| `src/statistics.py` | Full-tail summaries, independent age cohorts, group exclusion audits, monthly/annual counts |
| `src/repository_plots.py` | Repository profiles, adoption-age distributions/comparisons, repository trends |
| `src/tool_plots.py` | Category counts, trends, within-language presence and category-specific ages |
| `src/plotting.py` | Consistent accessible style, log1p ticks, captions and high-resolution PNG export |
| `src/pipeline.py`, `src/report.py` | Headless orchestration and generated findings/validation reports |
| `notebooks/sdd_analysis.ipynb` | Executed RQ-organized notebook with tables, figures and Markdown interpretation |
| `figures/` | 14 report-ready PNG figures |
| `results/` | Summary/source CSVs, figure manifest, validation/environment and execution/check reports |
| `tests/test_validation.py` | Lightweight real-data and synthetic regression checks |
| `ANALYSIS_FINDINGS.md` | Computed findings, limitations and final-report suggestions |

The optional category-age comparison is included. Optional language-by-ownership visualization is omitted to keep the core report focused. The category-language heatmap shows within-language percentages with explicit full-sample denominators; overlapping category shares need not add to 100%.

For sensitivity analysis, use `results/monthly_repository_counts_by_age_status.csv` and the group-specific age tables. These expose how predating histories and differential age exclusions affect interpretation without silently discarding observations.
