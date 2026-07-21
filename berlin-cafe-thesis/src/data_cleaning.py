"""
data_cleaning.py
================

Clean the raw Google Places café export into an analysis-ready dataset for the
Berlin café-location thesis.

The raw export (~176 columns) is reduced to the columns the analysis needs,
filtered to café venues, stripped of permanently closed and duplicate entries,
and annotated with a provisional "popular café" flag. The cleaned file is the
*target-variable source* for the pipeline; predictor features are built
separately from OpenStreetMap and Eurostat data to avoid circularity
(see docs/decision_log.md, D9).

Cleaning steps
--------------
1. Select and rename the relevant columns.
2. Filter to café venues (the "Moderate" definition; decision_log.md D6).
3. Remove permanently closed venues; keep temporarily closed ones, flagged (D7).
4. Remove duplicate venues.
5. Flag "popular" cafés: rating >= 4.2 AND reviews >= 100, provisional (D5).
   Spatial (Berlin) filtering is deferred to hexagon assignment (D8).
6. Validate and save.

Usage
-----
Run as a script (uses default project paths)::

    python src/data_cleaning.py

Or specify paths explicitly::

    python src/data_cleaning.py --input data/raw/berlin_cafes.csv \\
                                --output data/processed/cafes_clean.csv

Or import the function into a notebook::

    from src.data_cleaning import clean_cafes
    cafes = clean_cafes(pd.read_csv("data/raw/berlin_cafes.csv", low_memory=False))
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration
# (These constants could be moved into config.py; kept here so the module is
#  self-contained and reproducible on its own.)
# --------------------------------------------------------------------------- #

# Columns kept from the raw export, and the two we rename to plain names.
KEEP_COLS: list[str] = [
    "place_id", "title", "category_name", "location_lat", "location_lng",
    "total_score", "reviews_count", "postal_code", "city",
    "permanently_closed", "temporarily_closed", "scraped_at",
]
RENAME_COLS: dict[str, str] = {"total_score": "rating", "reviews_count": "n_reviews"}

# "Moderate" café definition: coffee-first venues plus bakery/pastry/donut.
# Excludes internet cafés, ice-cream shops, delis, bars, restaurants, etc.
KEEP_CATEGORIES: list[str] = [
    # coffee-first
    "Cafe", "Coffee shop", "Coffee roasters", "Coffee store", "Espresso bar",
    "Art cafe", "Chocolate cafe", "Children's cafe", "Vegetarian cafe and deli",
    "Restaurant or cafe", "Cafeteria",
    # bakery / pastry / donut (the Moderate add-on)
    "Bakery", "Pastry shop", "Patisserie", "Donut shop", "Cake shop",
]

# Provisional popularity thresholds (finalised after EDA; decision_log.md D5).
POPULAR_MIN_RATING: float = 4.2
POPULAR_MIN_REVIEWS: int = 100

# Default file locations relative to the project root.
DEFAULT_RAW = Path("data/raw/berlin_cafes.csv")
DEFAULT_OUT = Path("data/processed/cafes_clean.csv")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def find_project_root(marker: str = "requirements.txt") -> Path:
    """Return the project root by climbing upward until `marker` is found.

    This makes file paths work regardless of which sub-folder the code is run
    from, and on any machine (unlike a hard-coded absolute path).
    """
    for folder in [Path.cwd(), *Path.cwd().parents]:
        if (folder / marker).exists():
            return folder
    raise FileNotFoundError(f"Could not find '{marker}' above {Path.cwd()}")


def load_raw(path: Path) -> pd.DataFrame:
    """Load the raw café export."""
    df = pd.read_csv(path, low_memory=False)
    print(f"Raw dataset: {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


# --------------------------------------------------------------------------- #
# Cleaning
# --------------------------------------------------------------------------- #

def clean_cafes(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw café export and return an analysis-ready DataFrame.

    Prints a before -> after row count after each step so the effect of every
    cleaning decision is transparent (useful for auditing and for the thesis).
    """
    # 1. select and rename the relevant columns
    cafes = df[KEEP_COLS].rename(columns=RENAME_COLS)
    print(f"1. Selected columns          : {cafes.shape[1]} kept from {df.shape[1]}")

    # 2. filter to café venues (Moderate definition)
    before = len(cafes)
    cafes = cafes[cafes["category_name"].isin(KEEP_CATEGORIES)]
    print(f"2. Café filter               : {before:,} -> {len(cafes):,} "
          f"({len(cafes) - before:,})")

    # 3. drop permanently closed venues (keep temporarily closed, flagged)
    before = len(cafes)
    cafes = cafes[~cafes["permanently_closed"].astype(bool)]
    print(f"3. Drop permanently closed   : {before:,} -> {len(cafes):,} "
          f"({len(cafes) - before:,})")

    # 4. remove duplicates: primary on place_id, safety net on name + coords
    before = len(cafes)
    cafes = cafes.drop_duplicates(subset=["place_id"])
    cafes = cafes.drop_duplicates(subset=["title", "location_lat", "location_lng"])
    print(f"4. Deduplicate               : {before:,} -> {len(cafes):,} "
          f"({len(cafes) - before:,})")

    # 5. flag "popular" cafés (provisional threshold, pending EDA)
    #    NaN rating (cafés with 0 reviews) compares False, so they become 0.
    cafes["is_popular_prov"] = (
        (cafes["rating"] >= POPULAR_MIN_RATING)
        & (cafes["n_reviews"] >= POPULAR_MIN_REVIEWS)
    ).astype(int)
    print(f"5. Popular cafés (provisional): {cafes['is_popular_prov'].sum():,} "
          f"of {len(cafes):,}")

    return cafes


def validate(cafes: pd.DataFrame) -> None:
    """Assert the cleaning produced a well-formed dataset. Fails loudly if not."""
    assert cafes["place_id"].is_unique, "Duplicate place_ids remain"
    assert cafes["location_lat"].notna().all(), "Some cafés are missing coordinates"
    assert not cafes["permanently_closed"].astype(bool).any(), \
        "Permanently closed cafés remain"
    assert cafes["is_popular_prov"].isin([0, 1]).all(), "Popular flag is not 0/1"


# --------------------------------------------------------------------------- #
# Command-line entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the raw café dataset.")
    parser.add_argument("--input", type=Path, default=None,
                        help="Path to the raw CSV (default: data/raw/berlin_cafes.csv)")
    parser.add_argument("--output", type=Path, default=None,
                        help="Path for the clean CSV (default: data/processed/cafes_clean.csv)")
    args = parser.parse_args()

    # Resolve paths: use explicit args if given, otherwise anchor to project root.
    if args.input and args.output:
        raw_path, out_path = args.input, args.output
    else:
        root = find_project_root()
        raw_path = args.input or (root / DEFAULT_RAW)
        out_path = args.output or (root / DEFAULT_OUT)

    df = load_raw(raw_path)
    cafes = clean_cafes(df)
    validate(cafes)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cafes.to_csv(out_path, index=False)
    print(f"\nSaved {len(cafes):,} cafés -> {out_path}")


if __name__ == "__main__":
    main()