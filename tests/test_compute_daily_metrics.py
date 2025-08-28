import json
import sqlite3
import sys
from pathlib import Path


# Allow importing from src/
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import compute_daily_metrics as mod  # noqa: E402


def _setup_sample_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE sample_data (
            uid INTEGER,
            bike_number TEXT,
            start_time TEXT,
            end_time TEXT,
            start_station TEXT,
            end_station TEXT,
            duration INTEGER,
            distance REAL
        )
        """
    )
    # Rows for 2025-04-07 (the test day)
    rows = [
        # hour 00
        (1, "100", "2025-04-07 00:10:00", "2025-04-07 00:30:00", "A", "A", 10, 1.2),  # round trip, 10 min
        # hour 13
        (2, "101", "2025-04-07 13:00:00", "2025-04-07 13:20:00", "A", "B", 20, 2.5),
        (3, "102", "2025-04-07 13:15:00", "2025-04-07 13:45:00", "B", "A", 30, 3.0),
        # hour 14
        (4, "103", "2025-04-07 14:05:00", "2025-04-07 14:25:00", "B", "Poza stacją", 17, 2.0),
        # Another day (should be included when using --year)
        (5, "104", "2025-04-06 10:00:00", "2025-04-06 10:20:00", "C", "D", 25, 2.0),
    ]
    cur.executemany(
        "INSERT INTO sample_data (uid, bike_number, start_time, end_time, start_station, end_station, duration, distance) VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


def test_compute_metrics_core(tmp_path):
    db_path = tmp_path / "sample.db"
    _setup_sample_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        metrics = mod.compute_metrics(conn, "sample_data", "2025-04-07")
    finally:
        conn.close()

    assert metrics["date"] == "2025-04-07"
    assert metrics["total_rides"] == 4
    # Histogram: hours 0 -> 1 ride, 13 -> 2 rides, 14 -> 1 ride
    assert metrics["bike_rentals_histogram"].get("0") == 1
    assert metrics["bike_rentals_histogram"].get("13") == 2
    assert metrics["bike_rentals_histogram"].get("14") == 1

    # Distance/duration aggregates
    # Distances for 4 rides: 1.2 + 2.5 + 3.0 + 2.0 = 8.7
    assert abs(metrics["total_distance_km"] - 8.7) < 1e-6
    # Average distance ~ 2.175 -> rounded to 3 decimals
    assert metrics["avg_distance_km"] == 2.175

    # Durations (min): 10 + 20 + 30 + 17 = 77
    assert metrics["total_duration_min"] == 77
    # Average minutes = 19.25
    assert metrics["avg_duration_min"] == 19.25

    # Round trips: one (A->A)
    assert metrics["round_trips"] == 1
    # Left outside station: one
    assert metrics["left_outside_station"] == 1

    # Busiest stations: A and B each have 2 arrivals + 2 departures -> total 4, Poza stacją has 1 arrival
    top_names = [x["station"] for x in metrics["busiest_stations_top5"]]
    assert "A" in top_names and "B" in top_names

    # Top routes: expect (A->B) and (B->A) to be present with 1 each
    routes = {(x["start_station"], x["end_station"]): x["rides"] for x in metrics["top_routes_top5"]}
    assert routes.get(("A", "B")) == 1
    assert routes.get(("B", "A")) == 1


def test_main_writes_json(tmp_path):
    db_path = tmp_path / "sample.db"
    out_path = tmp_path / "out" / "metrics.json"
    _setup_sample_db(db_path)

    # Run CLI entry with custom paths and table (single day append -> yearly file)
    mod.main([
        "--date",
        "2025-04-07",
        "--db",
        str(db_path),
        "--table",
        "sample_data",
        "--out",
        str(out_path),
    ])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    # Structure: {"year": 2025, "days": {"YYYY-MM-DD": {...}}}
    assert data["year"] == 2025
    assert "2025-04-07" in data["days"]
    assert data["days"]["2025-04-07"]["total_rides"] == 4

    # Append second day and ensure merge
    mod.main([
        "--date",
        "2025-04-06",
        "--db",
        str(db_path),
        "--table",
        "sample_data",
        "--out",
        str(out_path),
    ])

    data2 = json.loads(out_path.read_text(encoding="utf-8"))
    assert set(data2["days"].keys()) >= {"2025-04-07", "2025-04-06"}


def test_year_mode_rebuild(tmp_path):
    db_path = tmp_path / "sample.db"
    out_path = tmp_path / "out" / "metrics_2025.json"
    _setup_sample_db(db_path)

    mod.main([
        "--year",
        "2025",
        "--db",
        str(db_path),
        "--table",
        "sample_data",
        "--out",
        str(out_path),
    ])

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["year"] == 2025
    # Should contain at least the two dates we inserted
    assert set(data["days"].keys()) >= {"2025-04-07", "2025-04-06"}
