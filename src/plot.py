"""Generate publication-quality charts from OpenAlex data."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from config import DATA_DIR, FIG_DIR, LAST_FULL_YEAR, COUNTRY_NAMES

# Seaborn styling
sns.set_theme(style="white", font_scale=1.1)
PALETTE = sns.color_palette("tab10")


def setup_fig(figsize=(12, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def save(fig, name):
    path = FIG_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  → {path}")


def plot_total_articles():
    """Bar chart of total articles per year with exponential trend."""
    df = pd.read_csv(DATA_DIR / "yearly_totals.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    fig, ax = setup_fig()

    ax.bar(full["year"], full["count"], color=PALETTE[0], width=0.8, edgecolor="none")

    # Exponential trend line
    x = np.array(full["year"] - full["year"].min(), dtype=float)
    y = np.array(full["count"], dtype=float)
    coeffs = np.polyfit(x, np.log(y), 1)
    trend_x = np.linspace(0, x.max(), 100)
    trend_y = np.exp(coeffs[1]) * np.exp(coeffs[0] * trend_x)
    trend_years = trend_x + full["year"].min()
    ax.plot(trend_years, trend_y, color="red", linewidth=2, linestyle="--",
            label=f"Exponential fit (r={coeffs[0]*100:.1f}%/yr)", zorder=5)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Articles")
    ax.set_title("Global Scientific Article Production (2000–2025)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left")
    save(fig, "total_articles_per_year.png")


def plot_yoy_growth():
    """Line chart of year-over-year growth rate."""
    df = pd.read_csv(DATA_DIR / "yearly_totals.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].sort_values("year").copy()
    full["yoy"] = full["count"].pct_change() * 100
    full = full.dropna()

    fig, ax = setup_fig()
    ax.plot(full["year"], full["yoy"], marker="o", markersize=5, color=PALETTE[0], linewidth=2)
    ax.axhline(y=5.6, color="red", linestyle="--", alpha=0.7, label="Hanson et al. reported rate (5.6%)")
    ax.axhline(y=0, color="gray", linestyle="-", alpha=0.3)

    ax.set_xlabel("Year")
    ax.set_ylabel("Year-over-Year Growth (%)")
    ax.set_title("Annual Growth Rate of Scientific Articles", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    save(fig, "yoy_growth_rate.png")


def plot_field_growth():
    """Stacked area chart of articles by domain."""
    df = pd.read_csv(DATA_DIR / "yearly_by_domain.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    pivot = full.pivot_table(index="year", columns="domain_name", values="count", aggfunc="sum").fillna(0)
    pivot = pivot.sort_index()

    fig, ax = setup_fig()
    ax.stackplot(pivot.index, [pivot[col] for col in pivot.columns],
                 labels=pivot.columns, alpha=0.85)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Articles")
    ax.set_title("Scientific Articles by Domain (2000–2025)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    save(fig, "field_growth_absolute.png")


def plot_field_growth_rates():
    """Horizontal bar chart of fastest-growing fields (2015→2025)."""
    df = pd.read_csv(DATA_DIR / "yearly_by_field.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    y1, y2 = 2015, LAST_FULL_YEAR
    f1 = full[full["year"] == y1].set_index("field_name")["count"]
    f2 = full[full["year"] == y2].set_index("field_name")["count"]
    growth = pd.DataFrame({"c_start": f1, "c_end": f2}).dropna()
    growth["growth_pct"] = (growth["c_end"] - growth["c_start"]) / growth["c_start"] * 100
    growth = growth.sort_values("growth_pct", ascending=True)  # ascending for horizontal bar

    fig, ax = setup_fig(figsize=(12, 8))
    ax.barh(growth.index, growth["growth_pct"], color="steelblue", edgecolor="none")

    ax.set_xlabel("Growth (%)")
    ax.set_title(f"Field Growth Rates ({y1}–{y2})", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    save(fig, "field_growth_rates.png")


def plot_field_share():
    """100% stacked area chart showing domain composition."""
    df = pd.read_csv(DATA_DIR / "yearly_by_domain.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    pivot = full.pivot_table(index="year", columns="domain_name", values="count", aggfunc="sum").fillna(0)
    pivot = pivot.sort_index()
    shares = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = setup_fig()
    ax.stackplot(shares.index, [shares[col] for col in shares.columns],
                 labels=shares.columns, alpha=0.85)

    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of Articles")
    ax.set_title("Domain Composition of Scientific Output", fontsize=14, fontweight="bold")
    ax.legend(loc="center right", fontsize=9)
    save(fig, "field_share_over_time.png")


def plot_top_countries():
    """Line chart for top 10 countries."""
    df = pd.read_csv(DATA_DIR / "yearly_by_country.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    # Find top 10 by latest year
    latest = full[full["year"] == LAST_FULL_YEAR]
    top10 = latest.nlargest(10, "count")["country_code"].tolist()

    fig, ax = setup_fig()
    for i, cc in enumerate(top10):
        sub = full[full["country_code"] == cc].sort_values("year")
        label = COUNTRY_NAMES.get(cc, cc)
        ax.plot(sub["year"], sub["count"], marker=".", linewidth=2, label=label, color=PALETTE[i % len(PALETTE)])

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Articles")
    ax.set_title("Top 10 Countries by Scientific Output (2000–2025)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    save(fig, "top_countries_over_time.png")


def plot_country_share():
    """Share of global output for top 5 countries over time."""
    df = pd.read_csv(DATA_DIR / "yearly_by_country.csv")
    full = df[df["year"] <= LAST_FULL_YEAR].copy()

    totals = pd.read_csv(DATA_DIR / "yearly_totals.csv")
    yearly_total = totals[totals["year"] <= LAST_FULL_YEAR].set_index("year")["count"]

    # Top 5 by latest year
    latest = full[full["year"] == LAST_FULL_YEAR]
    top5 = latest.nlargest(5, "count")["country_code"].tolist()

    fig, ax = setup_fig()
    for i, cc in enumerate(top5):
        country = full[full["country_code"] == cc].groupby("year")["count"].sum()
        share = (country / yearly_total * 100).dropna()
        label = COUNTRY_NAMES.get(cc, cc)
        ax.plot(share.index, share.values, linewidth=2.5, label=label,
                color=PALETTE[i], marker=".")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of Global Output (%)")
    ax.set_title("Global Share: Top 5 Countries (2000–2025)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "country_share_shift.png")


def main():
    FIG_DIR.mkdir(exist_ok=True)
    print("Generating charts...")
    plot_total_articles()
    plot_yoy_growth()
    plot_field_growth()
    plot_field_growth_rates()
    plot_field_share()
    plot_top_countries()
    plot_country_share()
    print("Done.")


if __name__ == "__main__":
    main()
