import os
import sqlite3
import sys
from pathlib import Path


# Import module from src
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import backfill_distance as mod  # noqa: E402


def _setup_db(path: Path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE bike_rides (
            uid INTEGER,
            bike_number TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            start_station TEXT,
            end_station TEXT,
            duration INTEGER,
            lat_start REAL,
            lon_start REAL,
            lat_end REAL,
            lon_end REAL,
            distance REAL
        )
        """
    )
    rows = [
        # Should be updated (valid coords, NULL distance)
        (1, "100", "2025-09-07 10:00:00", "2025-09-07 10:10:00", "A", "B", 10, 51.109782, 17.030175, 51.113871, 17.034484, None),
        # Should remain NULL (missing coords)
        (2, "101", "2025-09-07 10:00:00", "2025-09-07 10:10:00", "A", "B", 10, None, None, 51.113871, 17.034484, None),
        # Should remain unchanged (already set)
        (3, "102", "2025-09-07 10:00:00", "2025-09-07 10:10:00", "A", "B", 10, 51.109782, 17.030175, 51.113871, 17.034484, 9.999),
    ]
    cur.executemany(
        "INSERT INTO bike_rides (uid, bike_number, start_time, end_time, start_station, end_station, duration, lat_start, lon_start, lat_end, lon_end, distance) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_backfill_updates_only_null_distances(tmp_path):
    db_path = tmp_path / "bike.db"
    _setup_db(db_path)

    # Dry run first
    updated_dry = mod.backfill_distances(str(db_path), dry_run=True, do_backup=False)
    assert updated_dry == 1

    # Real run
    updated = mod.backfill_distances(str(db_path), dry_run=False, do_backup=False)
    assert updated == 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Row 1 updated
    cur.execute("SELECT distance FROM bike_rides WHERE uid=1")
    d1 = cur.fetchone()[0]
    assert d1 is not None and abs(d1 - 0.546) < 0.01
    # Row 2 remains NULL
    cur.execute("SELECT distance FROM bike_rides WHERE uid=2")
    assert cur.fetchone()[0] is None
    # Row 3 remains unchanged
    cur.execute("SELECT distance FROM bike_rides WHERE uid=3")
    assert abs(cur.fetchone()[0] - 9.999) < 1e-9
    conn.close()

