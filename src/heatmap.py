import datetime
import math
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

__all__ = ["generate_heatmap"]

MONTHS: List[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

COLORS = [
    [0.09, 0.11, 0.13, 1],
    [0.05, 0.27, 0.16, 1],
    [0.00, 0.43, 0.20, 1],
    [0.15, 0.65, 0.25, 1],
    [0.22, 0.83, 0.33, 1],
]

GITHUB_CMAP = ListedColormap(
    np.concatenate([np.linspace(x, y, 64) for x, y in zip(COLORS, COLORS[1:])])
)


def calculate_week_and_day_indices(offset: int, target: int) -> Tuple[int, int]:
    actual_day = target + offset
    weeks = actual_day // 7
    days = actual_day - (weeks * 7)

    return 6 - days, weeks


def create_heatmap(
    series: pd.Series, offset: int, weeks: int
) -> Tuple[np.ndarray, Dict[int, str]]:
    heatmap = np.zeros((7, weeks))
    ticks = {}
    for i, (date, value) in enumerate(series.items()):
        if date.day == 1:
            ticks[i // 7] = MONTHS[date.month - 1]

        day, week = calculate_week_and_day_indices(offset, i)
        heatmap[day, week] = value

    return heatmap, ticks


def blank_out_last_days(
    heatmap: np.ndarray, cmap, weeks: int, last_day: datetime.datetime
) -> None:
    if last_day.weekday() == 6:
        remaining = 6
    else:
        remaining = 6 - last_day.weekday() - 1

    cmap.set_under("#2f3136")
    for i in range(remaining):
        heatmap[i, weeks - 1] = -1


def stylized_axis(
    heatmap: np.ndarray, cmap, weeks: int, ticks: Dict[int, str]
) -> plt.Axes:
    y = np.arange(8) - 0.5
    x = np.arange(weeks + 1) - 0.5

    ax = plt.gca()
    mesh = ax.pcolormesh(x, y, heatmap, edgecolor="#2f3136", cmap=cmap, lw=2.5)

    ax.set_xticks(list(ticks.keys()))
    ax.set_xticklabels(list(ticks.values()))
    ax.xaxis.tick_top()
    ax.yaxis.set_ticks([])
    ax.tick_params(axis="x", colors="white")
    ax.set_aspect("equal")
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)

    plt.rcParams.update({"ytick.color": "white", "xtick.color": "white"})
    plt.sca(ax)
    plt.sci(mesh)
    plt.tick_params(length=0, width=0)

    return ax


def plot_heatmap(series: pd.Series, cmap: Optional[str]) -> plt.Axes:
    try:
        if cmap is None:
            cmap_obj = GITHUB_CMAP
        else:
            cmap_obj = plt.get_cmap(cmap)
    except ValueError:
        cmap_obj = GITHUB_CMAP

    last_day = max(series.keys())
    first_day = min(series.keys())

    offset = (first_day.weekday() + 1) % 7
    days = len(series) + offset
    weeks = math.ceil(days / 7)

    heatmap, ticks = create_heatmap(series, offset, weeks)

    blank_out_last_days(heatmap, cmap_obj, weeks, last_day)
    return stylized_axis(heatmap, cmap_obj, weeks, ticks)


def create_colorbar(mmax, mmin) -> None:
    plt.colorbar(ticks=np.linspace(mmin, mmax, 5, dtype=int), pad=0.02)


def generate_heatmap(series: pd.Series, cmap: Optional[str] = None) -> plt.Figure:
    figsize = plt.figaspect(7 / 56)
    fig = plt.figure(figsize=figsize, facecolor="#2f3136")
    _ = plot_heatmap(series, cmap)

    mmin = series.min()
    mmax = series.max()

    create_colorbar(mmax, mmin)

    plt.clim(mmin, mmax)

    return fig
