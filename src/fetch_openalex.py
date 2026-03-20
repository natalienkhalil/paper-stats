"""Fetch scientific publication data from OpenAlex API."""

import requests
import pandas as pd
import time
import sys

from config import DATA_DIR

BASE_URL = "https://api.openalex.org"
MAILTO = "email@example.com"
START_YEAR = 2000
END_YEAR = 2025
SLEEP_BETWEEN = 0.15
# has_doi:true restricts to DOI-indexed works (registered through providers such as Crossref and DataCite)
BASE_FILTER = "type:article,has_doi:true"


def fetch_with_retry(url, params, max_retries=3):
    """GET with polite pool, retry on 429."""
    params["mailto"] = MAILTO
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            wait = min(float(resp.headers.get("retry-after", 1)), 5)
            time.sleep(wait * (2 ** attempt))
            continue
        resp.raise_for_status()
        time.sleep(SLEEP_BETWEEN)
        return resp.json()
    raise Exception(f"Failed after {max_retries} retries: {url}")


def fetch_yearly_totals():
    """Single call → data/yearly_totals.csv"""
    print("Fetching yearly totals...")
    data = fetch_with_retry(
        f"{BASE_URL}/works",
        {"filter": BASE_FILTER, "group_by": "publication_year"},
    )
    rows = [
        {"year": int(item["key"]), "count": item["count"]}
        for item in data["group_by"]
        if item["key"].isdigit() and START_YEAR <= int(item["key"]) <= END_YEAR
    ]
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    df.to_csv(DATA_DIR / "yearly_totals.csv", index=False)
    print(f"  → {len(df)} years saved to yearly_totals.csv")
    return df


def fetch_yearly_by_field():
    """One call per year → data/yearly_by_domain.csv and data/yearly_by_field.csv"""
    print("Fetching by domain and field...")
    domain_rows = []
    field_rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        sys.stdout.write(f"\r  Domains & fields: {year}")
        sys.stdout.flush()
        year_filter = f"{BASE_FILTER},publication_year:{year}"

        # Domains (4 top-level)
        data = fetch_with_retry(
            f"{BASE_URL}/works",
            {"filter": year_filter, "group_by": "primary_topic.domain.id"},
        )
        for item in data["group_by"]:
            domain_rows.append({
                "year": year,
                "domain_id": item["key"],
                "domain_name": item["key_display_name"],
                "count": item["count"],
            })

        # Fields (more granular)
        data = fetch_with_retry(
            f"{BASE_URL}/works",
            {"filter": year_filter, "group_by": "primary_topic.field.id"},
        )
        for item in data["group_by"]:
            field_rows.append({
                "year": year,
                "field_id": item["key"],
                "field_name": item["key_display_name"],
                "count": item["count"],
            })

    print()
    pd.DataFrame(domain_rows).to_csv(DATA_DIR / "yearly_by_domain.csv", index=False)
    pd.DataFrame(field_rows).to_csv(DATA_DIR / "yearly_by_field.csv", index=False)
    print(f"  → yearly_by_domain.csv ({len(domain_rows)} rows)")
    print(f"  → yearly_by_field.csv ({len(field_rows)} rows)")


def fetch_yearly_by_country():
    """One call per year → data/yearly_by_country.csv"""
    print("Fetching by country...")
    rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        sys.stdout.write(f"\r  Countries: {year}")
        sys.stdout.flush()
        data = fetch_with_retry(
            f"{BASE_URL}/works",
            {
                "filter": f"{BASE_FILTER},publication_year:{year}",
                "group_by": "authorships.institutions.country_code",
            },
        )
        for item in data["group_by"]:
            raw_key = item["key"]
            if not raw_key or raw_key == "unknown":
                continue
            # OpenAlex returns URLs like https://openalex.org/countries/US
            cc = raw_key.split("/")[-1] if "/" in raw_key else raw_key
            rows.append({
                "year": year,
                "country_code": cc,
                "country_name": item["key_display_name"],
                "count": item["count"],
            })

    print()
    pd.DataFrame(rows).to_csv(DATA_DIR / "yearly_by_country.csv", index=False)
    print(f"  → yearly_by_country.csv ({len(rows)} rows)")


def main():
    DATA_DIR.mkdir(exist_ok=True)
    t0 = time.time()
    fetch_yearly_totals()
    fetch_yearly_by_field()
    fetch_yearly_by_country()
    print(f"\nDone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
