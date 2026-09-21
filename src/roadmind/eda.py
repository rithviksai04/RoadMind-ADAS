"""EDA plots + summary tables -> reports/eda/. Run: python -m roadmind.eda"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from roadmind.config import PROCESSED_DIR, REPORTS_DIR

OUT = REPORTS_DIR / "eda"
BLUE, GRID, INK = "#2a78d6", "#e3e2de", "#52514e"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": GRID,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "figure.dpi": 130, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_parquet(PROCESSED_DIR / "sample.parquet")
    full = json.loads((OUT / "full_dataset_stats.json").read_text())
    d["Start_Time"] = pd.to_datetime(d["Start_Time"], format="mixed")
    d["hour"] = d["Start_Time"].dt.hour
    d["year"] = d["Start_Time"].dt.year

    # 1. class balance (sample vs full)
    full_sev = pd.Series({int(k.split("|")[0]): 0 for k in full["full_strata_counts"]})
    for k, v in full["full_strata_counts"].items():
        full_sev[int(k.split("|")[0])] += v
    bal = pd.DataFrame({"full_pct": full_sev / full_sev.sum() * 100,
                        "sample_pct": d["Severity"].value_counts(normalize=True).sort_index() * 100})
    bal.round(3).to_csv(OUT / "class_balance.csv")
    fig, ax = plt.subplots(figsize=(6, 3.6))
    b = ax.bar(bal.index.astype(str), bal["sample_pct"], color=BLUE, width=0.55)
    for r, v in zip(b, bal["sample_pct"]):
        ax.text(r.get_x() + r.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=9)
    ax.set(xlabel="Severity (traffic-delay impact, not injury)", ylabel="% of rows",
           title="Class balance of Severity (400k stratified sample)")
    ax.grid(axis="x", visible=False)
    save(fig, "severity_balance.png")

    # 2. missingness on FULL data (from the chunked pass)
    miss = (pd.Series(full["full_null_counts"]) / full["full_rows"] * 100)
    miss = miss[miss > 0].sort_values()
    miss.round(2).to_csv(OUT / "missingness_full_pct.csv", header=["missing_pct"])
    fig, ax = plt.subplots(figsize=(7, 0.32 * len(miss) + 1))
    ax.barh(miss.index, miss.values, color=BLUE, height=0.6)
    ax.set(xlabel="% missing (full 7.7M rows)", title="Missing values per column")
    ax.grid(axis="y", visible=False)
    save(fig, "missingness.png")

    # 3. distributions (clipped to plausible ranges for display only)
    feats = {"Temperature(F)": (-30, 120), "Visibility(mi)": (0, 12), "Wind_Speed(mph)": (0, 50),
             "Humidity(%)": (0, 100), "Pressure(in)": (28, 31), "Precipitation(in)": (0, 0.5)}
    fig, axs = plt.subplots(2, 3, figsize=(11, 6))
    for ax, (c, (lo, hi)) in zip(axs.ravel(), feats.items()):
        ax.hist(d[c].dropna().clip(lo, hi), bins=40, color=BLUE)
        ax.set(title=c, yticks=[])
    fig.suptitle("Weather feature distributions (clipped for display)")
    save(fig, "weather_distributions.png")

    top = d["Weather_Condition"].value_counts().head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top.index, top.values, color=BLUE, height=0.6)
    ax.set(title="Top 15 Weather_Condition values", xlabel="rows in sample")
    ax.grid(axis="y", visible=False)
    save(fig, "weather_condition_top15.png")

    # 4. time features
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.6))
    h = d["hour"].value_counts().sort_index()
    axs[0].bar(h.index, h.values, color=BLUE)
    axs[0].set(title="Accidents by hour of day", xlabel="hour")
    w = d["Start_Time"].dt.dayofweek.value_counts().sort_index()
    axs[1].bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], w.values, color=BLUE)
    axs[1].set(title="Accidents by day of week")
    y = d["year"].value_counts().sort_index()
    axs[2].bar(y.index.astype(str), y.values, color=BLUE)
    axs[2].set(title="Accidents by year (2023 = Jan-Mar only)")
    save(fig, "time_distributions.png")

    # 5. severity-vs-feature tables (share of Severity 3-4 per group)
    d["high"] = (d["Severity"] >= 3).astype(int)
    tabs = {
        "by_source": d.groupby("Source")["high"].agg(["mean", "size"]),
        "by_hour": d.groupby("hour")["high"].agg(["mean", "size"]),
        "by_year": d.groupby("year")["high"].agg(["mean", "size"]),
        "by_weather_top": d[d["Weather_Condition"].isin(d["Weather_Condition"].value_counts().head(12).index)]
        .groupby("Weather_Condition")["high"].agg(["mean", "size"]).sort_values("mean"),
        "by_state_top": d[d["State"].isin(d["State"].value_counts().head(12).index)]
        .groupby("State")["high"].agg(["mean", "size"]).sort_values("mean"),
    }
    lines = ["# Share of Severity 3-4 (high delay impact) by group\n"]
    for k, t in tabs.items():
        lines += [f"## {k}\n", t.rename(columns={"mean": "share_sev34", "size": "n"}).round(3).to_markdown(), ""]
    (OUT / "severity_by_group.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(bal.round(3))
    print(miss.round(2).to_dict())


if __name__ == "__main__":
    main()
