"""Analyze OpenAlex publication data and print summary report."""

import numpy as np
import pandas as pd

from config import DATA_DIR, LAST_FULL_YEAR, COUNTRY_NAMES


def pct_change(old, new):
    if old == 0:
        return 0.0
    return (new - old) / old * 100


def fmt(n):
    """Format number with commas."""
    return f"{n:,.0f}"


def section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def validation(df):
    """Reproduce Hanson et al. 2024 result using OpenAlex."""
    section("VALIDATION (Hanson et al. 2024, Scopus+WoS, 2016→2022)")

    full = df[(df["year"] >= 2016) & (df["year"] <= 2022)].sort_values("year").copy()
    c16, c22 = full.iloc[0]["count"], full.iloc[-1]["count"]
    cumul = pct_change(c16, c22)
    full["yoy"] = full["count"].pct_change() * 100
    mean_yoy = full["yoy"].dropna().mean()

    # Exponential fit (log-linear OLS) for apples-to-apples comparison with Hanson's ~5.6%
    x = np.array(full["year"] - full["year"].min(), dtype=float)
    y = np.array(full["count"], dtype=float)
    coeffs = np.polyfit(x, np.log(y), 1)
    exp_rate = coeffs[0] * 100

    print(f"  Cumulative growth: {cumul:+.1f}%  |  Mean YoY: {mean_yoy:.1f}%  |  Exponential fit: {exp_rate:.1f}%/yr  (OpenAlex, DOI-indexed)")


def update(df):
    """Show what happened after Hanson's data ended (2022→2025)."""
    section(f"UPDATE (2022→{LAST_FULL_YEAR})")

    full = df[(df["year"] >= 2022) & (df["year"] <= LAST_FULL_YEAR)].sort_values("year").copy()
    c22, c_end = full.iloc[0]["count"], full.iloc[-1]["count"]
    cumul = pct_change(c22, c_end)
    full["yoy"] = full["count"].pct_change() * 100
    mean_yoy = full["yoy"].dropna().mean()

    print(f"  2022: {fmt(c22)} articles")
    print(f"  {LAST_FULL_YEAR}: {fmt(c_end)} articles")
    print(f"  Cumulative growth: {cumul:+.1f}%  |  Mean YoY: {mean_yoy:.1f}%")

    # Full-period cumulative growth
    c2000 = df[df["year"] == 2000]["count"].iloc[0]
    c_latest = df[df["year"] == LAST_FULL_YEAR]["count"].iloc[0]
    full_cumul = pct_change(c2000, c_latest)
    print(f"\n  Full period (2000→{LAST_FULL_YEAR}): {fmt(c2000)} → {fmt(c_latest)} ({full_cumul:+.1f}% cumulative, {c_latest/c2000:.1f}× increase)")


def yoy_growth(df):
    """Print year-over-year growth rates."""
    section("YEAR-OVER-YEAR GROWTH RATES")

    full = df[df["year"] <= LAST_FULL_YEAR].sort_values("year").copy()
    for i in range(1, len(full)):
        y = full.iloc[i]["year"]
        prev = full.iloc[i - 1]["count"]
        curr = full.iloc[i]["count"]
        yoy = pct_change(prev, curr)
        if y >= 2015:
            print(f"  {int(y)}: {yoy:+5.1f}%")


def field_analysis(df_domain):
    """Print domain and field-level analysis."""
    section("FIELD ANALYSIS (2015→2025)")

    full = df_domain[df_domain["year"] <= LAST_FULL_YEAR].copy()
    y1, y2 = 2015, LAST_FULL_YEAR

    d1 = full[full["year"] == y1].groupby("domain_name")["count"].sum()
    d2 = full[full["year"] == y2].groupby("domain_name")["count"].sum()

    combined = pd.DataFrame({"count_start": d1, "count_end": d2}).dropna()
    combined["growth_pct"] = (combined["count_end"] - combined["count_start"]) / combined["count_start"] * 100
    combined["added"] = combined["count_end"] - combined["count_start"]
    combined["share_start"] = combined["count_start"] / combined["count_start"].sum() * 100
    combined["share_end"] = combined["count_end"] / combined["count_end"].sum() * 100
    combined = combined.sort_values("count_end", ascending=False)

    header = f"{'Domain':<25} | {'Count '+str(y1):>12} | {'Count '+str(y2):>12} | {'Growth':>8} | {'Share '+str(y1):>9} | {'Share '+str(y2):>9}"
    print(header)
    print("-" * len(header))
    for name, row in combined.iterrows():
        print(
            f"{name:<25} | {fmt(row['count_start']):>12} | {fmt(row['count_end']):>12} | "
            f"{row['growth_pct']:>+7.1f}% | {row['share_start']:>8.1f}% | {row['share_end']:>8.1f}%"
        )

    fastest = combined["growth_pct"].idxmax()
    most_added = combined["added"].idxmax()
    print(f"\n  Fastest growing domain: {fastest} ({combined.loc[fastest, 'growth_pct']:+.1f}%)")
    print(f"  Most papers added:      {most_added} (+{fmt(combined.loc[most_added, 'added'])})")

    # Field-level breakdown (top 10 fastest growing)
    fields = pd.read_csv(DATA_DIR / "yearly_by_field.csv")
    fields_full = fields[fields["year"] <= LAST_FULL_YEAR].copy()
    f1 = fields_full[fields_full["year"] == y1].set_index("field_name")["count"]
    f2 = fields_full[fields_full["year"] == y2].set_index("field_name")["count"]
    fgrowth = pd.DataFrame({"count_start": f1, "count_end": f2}).dropna()
    fgrowth["growth_pct"] = (fgrowth["count_end"] - fgrowth["count_start"]) / fgrowth["count_start"] * 100
    fgrowth = fgrowth.sort_values("growth_pct", ascending=False).head(10)

    print(f"\nFastest growing fields ({y1}→{y2}):")
    for i, (name, row) in enumerate(fgrowth.iterrows(), 1):
        print(f"  {i:>2}. {name:<45} {fmt(row['count_start']):>10} → {fmt(row['count_end']):>10}  ({row['growth_pct']:+.1f}%)")


def country_analysis(df_country, df_totals):
    """Print country-level analysis."""
    section("COUNTRY ANALYSIS (2015→2025)")
    print("Note: Shares use total articles as denominator (whole counting).")
    print("A co-authored paper counts once per country, so shares sum to >100%.")

    full = df_country[df_country["year"] <= LAST_FULL_YEAR].copy()
    global_total = df_totals[df_totals["year"] == LAST_FULL_YEAR]["count"].iloc[0]

    # Top 15
    latest = full[full["year"] == LAST_FULL_YEAR].sort_values("count", ascending=False).head(15)
    print(f"\nTop 15 countries by {LAST_FULL_YEAR} output:")
    for i, (_, row) in enumerate(latest.iterrows(), 1):
        cc = row["country_code"]
        name = COUNTRY_NAMES.get(cc, cc)
        share = row["count"] / global_total * 100
        print(f"  {i:>2}. {cc} ({name:<20}): {fmt(row['count']):>12}  ({share:.1f}%)")

    # China vs US
    print("\nChina vs United States:")
    for year in range(2000, LAST_FULL_YEAR + 1):
        yr_data = full[full["year"] == year]
        cn = yr_data[yr_data["country_code"] == "CN"]["count"].sum()
        us = yr_data[yr_data["country_code"] == "US"]["count"].sum()
        if cn > us and year >= 2010:
            cn_prev = full[(full["year"] == year - 1) & (full["country_code"] == "CN")]["count"].sum()
            us_prev = full[(full["year"] == year - 1) & (full["country_code"] == "US")]["count"].sum()
            if cn_prev <= us_prev:
                print(f"  China surpassed the US in {year}")
            break

    cn_latest = full[(full["year"] == LAST_FULL_YEAR) & (full["country_code"] == "CN")]["count"].sum()
    us_latest = full[(full["year"] == LAST_FULL_YEAR) & (full["country_code"] == "US")]["count"].sum()
    print(f"  China {LAST_FULL_YEAR}: {fmt(cn_latest)} ({cn_latest/global_total*100:.1f}% of articles)")
    print(f"  US    {LAST_FULL_YEAR}: {fmt(us_latest)} ({us_latest/global_total*100:.1f}% of articles)")
    if cn_latest > 0 and us_latest > 0:
        print(f"  China/US ratio: {cn_latest/us_latest:.2f}x")

    # Fastest growing countries
    print(f"\nFastest growing countries (2015→{LAST_FULL_YEAR}, min 10k papers in 2015):")
    c2015 = full[full["year"] == 2015].set_index("country_code")["count"]
    clatest = full[full["year"] == LAST_FULL_YEAR].set_index("country_code")["count"]
    growth = pd.DataFrame({"c2015": c2015, "clatest": clatest}).dropna()
    growth = growth[growth["c2015"] >= 10000]
    growth["growth_pct"] = (growth["clatest"] - growth["c2015"]) / growth["c2015"] * 100
    growth = growth.sort_values("growth_pct", ascending=False).head(10)

    for i, (cc, row) in enumerate(growth.iterrows(), 1):
        name = COUNTRY_NAMES.get(cc, cc)
        print(f"  {i:>2}. {cc} ({name}): {row['growth_pct']:+.1f}%")


def main():
    totals = pd.read_csv(DATA_DIR / "yearly_totals.csv")
    domains = pd.read_csv(DATA_DIR / "yearly_by_domain.csv")
    countries = pd.read_csv(DATA_DIR / "yearly_by_country.csv")

    validation(totals)
    update(totals)
    yoy_growth(totals)
    field_analysis(domains)
    country_analysis(countries, totals)


if __name__ == "__main__":
    main()
