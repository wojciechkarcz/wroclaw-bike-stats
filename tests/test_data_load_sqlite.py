import os
import sys
import shutil
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import sqlite3
import pytest

# Ensure we can import from the src/ directory regardless of cwd
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
import data_load_sqlite as mod


def test_extract_dt_from_filename_and_pick_latest():
    names = [
        "Historia_przejazdow_2025-4-10_16_27_30.csv",
        "Historia_przejazdow_2025-5-24_17_3_13.csv",
        "Historia_przejazdow_2025-5-23_17_2_13.csv",
    ]
    urls = [f"https://example.com/{n}" for n in names]
    latest_url, latest_name = mod.pick_latest_csv(urls)
    assert latest_url.endswith("Historia_przejazdow_2025-5-24_17_3_13.csv")
    assert latest_name == "Historia_przejazdow_2025-5-24_17_3_13.csv"


def test_transform_data_distance_and_columns(tmp_path):
    stations_path = tmp_path / "stations.csv"
    stations_path.write_text(
        "station_name,lat,lon\nLegnicka (Park Magnolia),51.122,16.987\nRynek,51.110,17.032\n",
        encoding="utf-8",
    )
    df = pd.DataFrame(
        {
            "UID wynajmu": [1, 2],
            "Numer roweru": ["100", "101"],
            "Data wynajmu": ["2025-04-07 13:52:45", "2025-04-07 13:59:45"],
            "Data zwrotu": ["2025-04-07 14:00:00", "2025-04-07 14:05:00"],
            "Stacja wynajmu": ["Legnicka (Park Magnolia)", "Rynek"],
            "Stacja zwrotu": ["Rynek", "Legnicka (Park Magnolia)"],
            "Czas trwania": [1304, 900],
        }
    )
    cleaned = mod.transform_data(df, str(stations_path))
    # Required columns present
    for col in [
        "uid",
        "bike_number",
        "start_time",
        "end_time",
        "start_station",
        "end_station",
        "duration",
        "lat_start",
        "lon_start",
        "lat_end",
        "lon_end",
        "distance",
    ]:
        assert col in cleaned.columns
    # Types coerced
    assert pd.api.types.is_integer_dtype(cleaned["uid"].dtype)
    assert pd.api.types.is_datetime64_any_dtype(cleaned["start_time"].dtype)
    # Distance computed and non-null
    assert cleaned["distance"].notna().all()


def test_main_uses_spec_paths_and_writes_outputs(monkeypatch, tmp_path):
    # Prepare a local raw CSV to simulate download
    sample_raw = os.path.join(
        str(REPO_ROOT),
        "data",
        "raw",
        "2025",
        "Historia_przejazdow_2025-5-24_17_3_13.csv",
    )
    if not os.path.exists(sample_raw):
        # Fallback: pick any CSV in raw/2025 if exact one missing
        raw_dir = os.path.join(str(REPO_ROOT), "data", "raw", "2025")
        sample_raw = next(
            (os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(".csv")),
            None,
        )
        assert sample_raw is not None, "No sample raw CSV found in data/raw/2025"

    # Capture paths used by to_csv and load_to_sqlite
    used = SimpleNamespace(cleaned_path=None, db_path=None)

    def fake_get_all_csv_urls(page_url, session):
        return [
            "https://example.com/Historia_przejazdow_2025-5-24_17_3_13.csv",
            "https://example.com/Historia_przejazdow_2025-5-23_17_2_13.csv",
        ]

    def fake_download_file(url, out_dir, session):
        # Simulate download by copying the sample file into out_dir
        os.makedirs(out_dir, exist_ok=True)
        dst = os.path.join(out_dir, os.path.basename(sample_raw))
        if not os.path.exists(dst):
            shutil.copy2(sample_raw, dst)
        return dst

    real_to_csv = pd.DataFrame.to_csv

    def spy_to_csv(self, path, *a, **kw):
        used.cleaned_path = path
        return real_to_csv(self, path, *a, **kw)

    # keep original to call through
    orig_load_to_sqlite = mod.load_to_sqlite

    def spy_load_to_sqlite(df, db_path):
        used.db_path = db_path
        # actually create the DB and load (to validate it works)
        return orig_load_to_sqlite(df, db_path)

    # Monkeypatch
    monkeypatch.setattr(mod, "get_all_csv_urls", fake_get_all_csv_urls)
    monkeypatch.setattr(mod, "download_file", fake_download_file)
    monkeypatch.setattr(pd.DataFrame, "to_csv", spy_to_csv)
    monkeypatch.setattr(mod, "load_to_sqlite", spy_load_to_sqlite)

    # Run
    mod.main()

    # Assertions on paths according to SPECS
    assert used.cleaned_path is not None and "data/interim/" in used.cleaned_path.replace("\\", "/")
    assert used.db_path is not None and used.db_path.replace("\\", "/").endswith("data/processed/bike_data.db")

    # Validate DB exists and has the table
    assert os.path.exists(used.db_path)
    conn = sqlite3.connect(used.db_path)
    try:
        cur = conn.execute("SELECT count(*) FROM bike_rides")
        count = cur.fetchone()[0]
        assert count >= 0
    finally:
        conn.close()
