import os
import sys
from typing import List

import pandas as pd

# Ensure we can import sibling module when run as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from data_load_sqlite import (
    repo_root,
    ensure_dir,
    transform_data,
    load_to_sqlite,
)


def list_raw_csvs(raw_dir: str) -> List[str]:
    if not os.path.isdir(raw_dir):
        return []
    return sorted(
        [
            os.path.join(raw_dir, f)
            for f in os.listdir(raw_dir)
            if f.lower().endswith(".csv")
        ]
    )


def main():
    root = repo_root()

    # Paths per docs/SPECS.md directory contract
    db_path = os.path.join(root, "data", "processed", "bike_data.db")
    stations_csv = os.path.join(root, "data", "bike_stations.csv")
    raw_dir = os.path.join(root, "data", "raw", "2025")
    interim_dir = os.path.join(root, "data", "interim")

    ensure_dir(os.path.dirname(db_path))
    ensure_dir(interim_dir)

    csv_files = list_raw_csvs(raw_dir)
    if not csv_files:
        raise SystemExit(f"No CSV files found in {raw_dir}")

    print(f"Found {len(csv_files)} raw CSV files in {raw_dir}")
    total_rows = 0
    processed = 0

    for path in csv_files:
        fname = os.path.basename(path)
        print(f"\nReading raw CSV: {fname}")
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except Exception as e:
            print(f"  Skipping {fname}: failed to read CSV ({e})")
            continue

        print("  Transforming data...")
        try:
            cleaned = transform_data(df, stations_csv)
        except Exception as e:
            print(f"  Skipping {fname}: transform failed ({e})")
            continue

        cleaned_name = os.path.splitext(fname)[0] + "_clean.csv"
        cleaned_path = os.path.join(interim_dir, cleaned_name)
        cleaned.to_csv(cleaned_path, index=False)
        print(f"  Wrote cleaned CSV: {cleaned_path}")

        print("  Loading into SQLite...")
        try:
            load_to_sqlite(cleaned, db_path)
        except Exception as e:
            print(f"  Loading failed for {fname}: {e}")
            continue

        processed += 1
        total_rows += len(cleaned)
        print(f"  Done: {len(cleaned)} rows (duplicates ignored by uid)")

    print(
        f"\nCompleted. Processed {processed}/{len(csv_files)} files. "
        f"Total staged rows: {total_rows}. DB: {db_path}"
    )


if __name__ == "__main__":
    main()

