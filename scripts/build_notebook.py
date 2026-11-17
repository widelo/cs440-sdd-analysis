"""Generate the RQ-organized analysis notebook; execution is a separate step."""
from pathlib import Path
import nbformat as nbf


def build(root: Path) -> None:
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    cells = [md("""# Spec-driven development in GitHub repositories

CSU CS 440 final project · cleaned SpecMine exploratory analysis

**Questions:** RQ1 repository profiles; RQ2 repository age at first detection; RQ3 detections and category use over time.

First detected specification commits are a **proxy for adoption**. These tables contain detected SDD repositories, without a GitHub-wide comparison population. Counts and shares describe this sample, not overall GitHub adoption rates or causal effects. Data end in **July 2026**; July and 2026 are partial.

The repository table has one row per repository. The category table has one row per repository-category pair, and memberships overlap. Generic categories such as `root_bare` and `docs_embedded` are not software products. All analyses follow `DATA_COLUMNS.md`."""),
    code("""from pathlib import Path
import sys
ROOT = Path.cwd().resolve()
if not (ROOT / 'data/repo_summary.csv').exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from IPython.display import display, Markdown, Image
from src.data import load_data
from src.statistics import summary_tables
from src.plotting import set_style
from src import repository_plots as rp, tool_plots as tp

print((ROOT / 'DATA_COLUMNS.md').read_text(encoding='utf-8'))
data = load_data(ROOT)  # validation precedes all analysis
r, t = data.repositories, data.tools
tables = summary_tables(data)
OUT = ROOT / 'figures'
set_style()

def show(chart):
    display(Image(filename=str(chart.path), width=950))
    display(Markdown('**Caption.** ' + chart.caption + '\\n\\n**Interpretation.** ' + chart.interpretation))

display(Markdown(f'Validated **{len(r):,} repositories** and **{len(t):,} repository-category pairs** across **{t.repo_name.nunique():,} unique repositories**.'))
display(tables['age_status_audit'])
display(Markdown('**Input SHA-256 fingerprints:** ' + str(data.audit['input_sha256'])))"""),
    md("""## RQ1: What types of GitHub repositories use detected SDD?

Use every repository row, irrespective of adoption-age status. Numeric summaries retain all nonmissing observations and outliers. Logged-in specification contributor counts refer to unique GitHub accounts committing to detected specification files, not the entire repository contributor population."""),
    code("display(tables['numeric_summary'].query(\"grain == 'repository'\"))")]
    sections = [
        ("Top languages and missingness", "rp.languages(r, OUT)"),
        ("Repository owner types", "rp.ownership(r, OUT)"),
        ("Stars and forks received", "rp.popularity(r, OUT)"),
        ("Specification files per repository", "rp.specifications(r, OUT)"),
        ("Logged-in specification contributors", "rp.contributors(r, OUT)")]
    for title, expr in sections:
        cells += [md("### " + title), code(f"show({expr})")]
    cells += [md("""## RQ2: At what repository age is SDD first detected?

Repository ages use **only `adoption_age_status == 'valid'`**. Category ages independently use **only `tool_adoption_age_status == 'valid'`**. No global filtering is applied. Raw negative ages and rounded `-0.0` cannot override status. Plots disclose total inclusions/exclusions and show valid group sizes. Group tables also report excluded statuses per group. IQRs describe distributions, not confidence intervals."""),
        code("display(tables['age_status_audit'])\ndisplay(tables['numeric_summary'].query(\"grain.str.contains('valid ages')\", engine='python'))"),
        md("### Valid repository adoption-age distribution"), code("show(rp.adoption_age_distribution(r, OUT))"),
        md("### Adoption age by owner type"), code("display(tables['age_by_ownership'])\nshow(rp.age_groups(r, OUT))"),
        md("### Adoption age for common programming languages"), code("display(tables['age_by_language'])\nshow(rp.age_groups(r, OUT, 'repo_language'))"),
        md("### Optional: category-specific adoption ages"), code("display(tables['age_by_category'])\nshow(tp.category_ages(t, OUT))"),
        md("""## RQ3: How have detected adoption and category use changed over time?

Repository trends use `first_sdd_at`/`adoption_year`; category trends use `first_tool_adoption_at`. Dated predating records remain included because time trends do not require valid repository ages. Missing first-detection dates cannot be assigned to a period. Each repository contributes once to the repository trend, and once per category to category trends. These are first detections, **not monthly active usage**. July 2026 and the 2026 calendar year are incomplete; the last observed commit is not a verified collection cutoff."""),
        md("### Monthly repository first detections"), code("show(rp.monthly_adoption(r, OUT))"),
        md("### Annual repository first detections"), code("display(tables['annual_repository_counts'])\nshow(rp.annual_adoption(r, OUT))"),
        md("### Common detected SDD categories"), code("display(tables['numeric_summary'].query(\"variable == 'num_specs_for_tool'\"))\nshow(tp.common_categories(t, OUT))"),
        md("### Monthly first detections for leading categories"), code("show(tp.monthly_categories(t, OUT))"),
        md("### Category presence within main programming languages"), code("show(tp.categories_by_language(r, t, OUT))"),
        md("""### Sensitivity to predating histories

The following table separates dated repository first detections by age status. It permits a valid-only sensitivity comparison without discarding predating records from the main time analysis. Missing-date rows cannot appear here."""),
        code("display(tables['monthly_repository_counts_by_age_status'])"),
        md("""## Limitations and report guidance

- The sampling frame and detection process limit generalization. There is no denominator for overall GitHub adoption, no causal comparison, and no monthly activity/retention measure.
- `repo_fork` is uniformly False/0, preventing fork-vs-non-fork comparisons. `repo_forks` is a separate numeric measure of forks received.
- Missing languages are an explicit bucket in RQ1. Language comparisons use top known languages with stated denominators. Category memberships overlap; within-language percentages need not sum to 100%.
- Stars and forks are snapshot counts. Main language is not a full language inventory. Specifications and contributors reflect detected files and logged-in accounts.
- Ages are conditional on usable chronology; per-group exclusion counts should accompany comparisons. Imported/migrated histories may help explain predating commits but cannot be established from these tables.
- Use medians/IQRs with full-tail means/maxima; log1p plots preserve zero. Do not interpret the partial final-month drop as an adoption decline or annualize 2026 without verified coverage.

Run `python -m src.pipeline` to regenerate all tables, figures and the dynamic `ANALYSIS_FINDINGS.md`. See `DATA_VALIDATION.md` and `results/validation_report.json` for the validation audit.""")]
    notebook = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {
        "display_name": "Python 3 (SDD analysis)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"}})
    nbf.validate(notebook)
    nbf.write(notebook, root / "notebooks/sdd_analysis.ipynb")


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1])
