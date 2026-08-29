#!/usr/bin/env python3
"""
fetch_yc_batches.py

Fetches entire Y Combinator company directory data across all batches
(Winter, Spring, Summer, Fall) using the public YC Algolia API and saves
one CSV file per batch inside the 'data/yc_bacthes/' folder.
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output even on Windows command prompt
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = SCRIPT_DIR / "data/yc_bacthes"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
YC_COMPANIES_URL = "https://www.ycombinator.com/companies"
DEFAULT_ALGOLIA_APP = "45BWZJ1SGC"
DEFAULT_ALGOLIA_KEY = "NzllNTY5MzJiZGM2OTY2ZTQwMDEzOTNhYWZiZGRjODlhYzVkNjBmOGRjNzJiMWM4ZTU0ZDlhYTZjOTJiMjlhMWFuYWx5dGljc1RhZ3M9eWNkYyZyZXN0cmljdEluZGljZXM9WUNDb21wYW55X3Byb2R1Y3Rpb24lMkNZQ0NvbXBhbnlfQnlfTGF1bmNoX0RhdGVfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVE"
INDEX_NAME = "YCCompany_production"

CSV_COLUMNS = [
    "id",
    "name",
    "slug",
    "batch",
    "status",
    "one_liner",
    "long_description",
    "website",
    "ycdc_company_url",
    "all_locations",
    "team_size",
    "industry",
    "subindustry",
    "industries",
    "tags",
    "regions",
    "stage",
    "top_company",
    "isHiring",
    "nonprofit",
    "former_names",
    "small_logo_thumb_url",
    "launched_at",
]


def fetch_algolia_credentials() -> Tuple[str, str]:
    """Dynamically fetches latest Algolia App ID and Search API Key from YC website."""
    req = urllib.request.Request(
        YC_COMPANIES_URL,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
            match = re.search(r"window\.AlgoliaOpts\s*=\s*(\{.*?\});", html)
            if match:
                opts = json.loads(match.group(1))
                app_id = opts.get("app", DEFAULT_ALGOLIA_APP)
                api_key = opts.get("key", DEFAULT_ALGOLIA_KEY)
                return app_id, api_key
    except Exception as e:
        print(
            f"[Warning] Failed to dynamically scrape Algolia credentials ({e}). Using default keys."
        )
    return DEFAULT_ALGOLIA_APP, DEFAULT_ALGOLIA_KEY


def execute_algolia_query(app_id: str, api_key: str, params: str) -> Dict[str, Any]:
    """Executes a search query against Algolia REST API."""
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/*/queries"
    headers = {
        "x-algolia-application-id": app_id,
        "x-algolia-api-key": api_key,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    payload = {
        "requests": [
            {
                "indexName": INDEX_NAME,
                "params": params,
            }
        ]
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["results"][0]


def get_all_available_batches(app_id: str, api_key: str) -> Dict[str, int]:
    """Retrieves all available batches and company counts from the Algolia facet index."""
    params = "query=&hitsPerPage=1&facets=batch&maxValuesPerFacet=1000"
    res = execute_algolia_query(app_id, api_key, params)
    batches = res.get("facets", {}).get("batch", {})
    return batches


def fetch_companies_for_batch(
    app_id: str, api_key: str, batch_name: str
) -> List[Dict[str, Any]]:
    """Fetches all company records belonging to a specific batch with pagination."""
    companies = []
    page = 0
    hits_per_page = 1000

    while True:
        facet_filter = json.dumps([f"batch:{batch_name}"])
        encoded_filter = urllib.parse.quote(facet_filter)
        params = f"query=&hitsPerPage={hits_per_page}&page={page}&facetFilters={encoded_filter}"
        res = execute_algolia_query(app_id, api_key, params)
        hits = res.get("hits", [])
        if not hits:
            break

        companies.extend(hits)
        nb_pages = res.get("nbPages", 1)
        page += 1
        if page >= nb_pages:
            break

    return companies


def transform_company_to_row(company: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens and formats a single company hit into a structured CSV row."""
    slug = company.get("slug") or ""
    ycdc_url = f"https://www.ycombinator.com/companies/{slug}" if slug else ""

    def list_to_str(val: Any) -> str:
        if isinstance(val, list):
            return ", ".join(str(item) for item in val if item)
        return str(val) if val is not None else ""

    return {
        "id": company.get("id", ""),
        "name": company.get("name", ""),
        "slug": slug,
        "batch": company.get("batch", ""),
        "status": company.get("status", ""),
        "one_liner": company.get("one_liner", "") or "",
        "long_description": company.get("long_description", "") or "",
        "website": company.get("website", "") or "",
        "ycdc_company_url": ycdc_url,
        "all_locations": company.get("all_locations", "") or "",
        "team_size": company.get("team_size", "") or "",
        "industry": company.get("industry", "") or "",
        "subindustry": company.get("subindustry", "") or "",
        "industries": list_to_str(company.get("industries")),
        "tags": list_to_str(company.get("tags")),
        "regions": list_to_str(company.get("regions")),
        "stage": company.get("stage", "") or "",
        "top_company": company.get("top_company", False),
        "isHiring": company.get("isHiring", False),
        "nonprofit": company.get("nonprofit", False),
        "former_names": list_to_str(company.get("former_names")),
        "small_logo_thumb_url": company.get("small_logo_thumb_url", "") or "",
        "launched_at": company.get("launched_at", "") or "",
    }


def sanitize_batch_filename(batch_name: str) -> str:
    """Converts a batch name like 'Winter 2024' or 'Summer 2021' to '{year}_{season}.csv' (e.g. '2024_Winter.csv')."""
    match = re.search(
        r"^(Winter|Spring|Summer|Fall)\s+(\d{4})$", batch_name.strip(), re.IGNORECASE
    )
    if match:
        season, year = match.group(1).title(), match.group(2)
        return f"{year}_{season}.csv"
    safe_name = re.sub(r"[^\w\s-]", "", batch_name).strip()
    safe_name = re.sub(r"[\s]+", "_", safe_name)
    return f"{safe_name}.csv"


def sort_batch_key(batch_name: str) -> Tuple[int, int]:
    """Helper to sort batches chronologically (Year, Season)."""
    season_order = {"Winter": 1, "Spring": 2, "Summer": 3, "Fall": 4}
    match = re.search(
        r"(Winter|Spring|Summer|Fall)\s+(\d{4})", batch_name, re.IGNORECASE
    )
    if match:
        season, year = match.group(1).title(), int(match.group(2))
        return (year, season_order.get(season, 0))
    return (0, 0)


def save_batch_csv(filepath: Path, rows: List[Dict[str, Any]]) -> None:
    """Writes company rows to a CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Download Y Combinator company directory data for all batches (Winter, Spring, Summer, Fall) into separate CSV files."
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=str(DEFAULT_DATA_DIR),
        help=f"Directory to save batch CSV files (default: '{DEFAULT_DATA_DIR}').",
    )
    parser.add_argument(
        "--season",
        "-s",
        type=str,
        choices=["Winter", "Spring", "Summer", "Fall", "All"],
        default="All",
        help="Filter specific season or 'All' for all batches (default: All).",
    )
    parser.add_argument(
        "--batch",
        "-b",
        type=str,
        default=None,
        help="Fetch a single specific batch (e.g. 'Winter 2024' or 'Summer 2023').",
    )
    args = parser.parse_args()

    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("[*] Y Combinator Batch Data Fetcher")
    print("=" * 60)
    print("[1/3] Fetching Algolia API credentials...")
    app_id, api_key = fetch_algolia_credentials()
    print(f"      App ID: {app_id}")

    print("[2/3] Retrieving list of all YC batches...")
    batches_dict = get_all_available_batches(app_id, api_key)
    print(f"      Found {len(batches_dict)} total batches.")

    sorted_batches = sorted(batches_dict.keys(), key=sort_batch_key, reverse=True)

    # Filter batches if requested
    if args.batch:
        target_batches = [b for b in sorted_batches if b.lower() == args.batch.lower()]
        if not target_batches:
            print(
                f"[Error] Batch '{args.batch}' not found. Available: {sorted_batches}"
            )
            sys.exit(1)
    elif args.season != "All":
        target_batches = [
            b for b in sorted_batches if b.lower().startswith(args.season.lower())
        ]
    else:
        target_batches = sorted_batches

    print(
        f"[3/3] Downloading {len(target_batches)} batches to '{output_path.resolve()}'..."
    )
    total_companies = 0
    all_summary = []

    for idx, batch_name in enumerate(target_batches, 1):
        expected_count = batches_dict.get(batch_name, 0)
        filename = sanitize_batch_filename(batch_name)
        file_path = output_path / filename

        print(
            f"  [{idx:2d}/{len(target_batches)}] Fetching {batch_name:<15} (~{expected_count} companies)...",
            end="",
            flush=True,
        )
        try:
            hits = fetch_companies_for_batch(app_id, api_key, batch_name)
            rows = [transform_company_to_row(c) for c in hits]
            save_batch_csv(file_path, rows)
            count = len(rows)
            total_companies += count
            all_summary.append(
                {"Batch": batch_name, "Companies": count, "File": filename}
            )
            print(f" saved {count} companies -> {filename}")
        except Exception as e:
            print(f" failed ({e})")

        # Brief pause between batches
        time.sleep(0.05)

    print("\n" + "=" * 60)
    print(
        f"[+] Finished! Successfully saved {total_companies:,} companies across {len(target_batches)} batches."
    )
    print(f"[+] Output directory: {output_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
