"""Accessible plot style, original-unit log ticks and publication PNG export."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns

BLUE = "#0072B2"
ORANGE = "#D55E00"
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


@dataclass
class Chart:
    """A saved figure, its reproducible source table and dynamic interpretation."""
    name: str
    path: Path
    caption: str
    interpretation: str
    table: pd.DataFrame


def set_style() -> None:
    """Apply a consistent colorblind-accessible style in scripts and notebooks."""
    sns.set_theme(style="whitegrid", context="notebook", palette=PALETTE,
                  rc={"font.family": "DejaVu Sans", "axes.spines.top": False,
                      "axes.spines.right": False, "grid.alpha": .25,
                      "axes.titleweight": "bold", "figure.dpi": 110})


def finish(fig: Figure, name: str, out: Path, caption: str,
           interpretation: str, table: pd.DataFrame) -> Chart:
    """Save a 300-DPI PNG with an embedded methodological caption; close figure."""
    out.mkdir(parents=True, exist_ok=True)
    lines = textwrap.fill(caption, width=118)
    bottom = .07 + .025 * (lines.count("\n") + 1)
    fig.tight_layout(rect=(0, bottom, 1, 1), pad=1.4)
    fig.text(.025, .02, lines, ha="left", va="bottom", fontsize=8, color="#333333")
    path = out / f"{name}.png"
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return Chart(name, path, caption, interpretation, table)


def bar_labels(ax: plt.Axes, horizontal: bool = True) -> None:
    """Annotate counts and leave space for labels."""
    for container in ax.containers:
        ax.bar_label(container, fmt=lambda v: f"{v:,.0f}", padding=4, fontsize=9)
    if horizontal:
        ax.set_xlim(0, ax.get_xlim()[1] * 1.15)
    else:
        ax.set_ylim(0, ax.get_ylim()[1] * 1.15)


def log_ticks(ax: plt.Axes, maximum: float, axis: str = "x", ages: bool = False) -> None:
    """Label a log1p-transformed axis in original units, retaining zero."""
    candidates = [0, 1, 7, 30, 90, 365, 1000, 3650, 10000, 30000] if ages else [0, 1, 10, 100, 1000, 10000, 100000, 1000000]
    ticks = [v for v in candidates if v <= maximum]
    setter = ax.set_xticks if axis == "x" else ax.set_yticks
    setter(np.log1p(ticks), [f"{v:,}" for v in ticks])
