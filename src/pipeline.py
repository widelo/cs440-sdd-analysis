"""Run the full headless analysis: python -m src.pipeline [--root PATH]."""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import platform

from .data import load_data
from .plotting import set_style
from . import repository_plots as rp, tool_plots as tp
from .statistics import summary_tables
from .report import write_reports


def run(root: Path) -> None:
    """Validate before computing statistics or writing any analysis artifacts."""
    data = load_data(root)
    r, t = data.repositories, data.tools
    out, tables_dir = root / "figures", root / "results"
    tables_dir.mkdir(exist_ok=True)
    tables = summary_tables(data)
    for name, table in tables.items():
        table.to_csv(tables_dir / f"{name}.csv", index=table.index.name is not None)
    set_style()
    charts = [rp.languages(r, out), rp.ownership(r, out), rp.popularity(r, out),
        rp.specifications(r, out), rp.contributors(r, out), rp.adoption_age_distribution(r, out),
        rp.age_groups(r, out), rp.age_groups(r, out, "repo_language"), tp.category_ages(t, out),
        rp.monthly_adoption(r, out), rp.annual_adoption(r, out), tp.common_categories(t, out),
        tp.monthly_categories(t, out), tp.categories_by_language(r, t, out)]
    manifest = []
    for chart in charts:
        chart.table.to_csv(tables_dir / f"{chart.name}_plot_data.csv", index=True)
        manifest.append({"figure": str(chart.path.relative_to(root)), "caption": chart.caption,
                         "interpretation": chart.interpretation})
    data.audit["environment"] = {"python": platform.python_version(), **{
        name: version(name) for name in ("pandas", "numpy", "matplotlib", "seaborn", "nbformat", "nbclient")}}
    (tables_dir / "validation_report.json").write_text(json.dumps(data.audit, indent=2), encoding="utf-8")
    (tables_dir / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_reports(root, data, tables, charts)
    print(f"Validated {len(r):,} repositories and {len(t):,} repository-category rows; saved {len(charts)} PNGs and {len(tables)} summary tables.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    run(parser.parse_args().root.resolve())
