import shutil
import json
import sqlite3
import sys
from pathlib import Path
import os

# allow importing from src
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import bike_status_changes as mod  # noqa: E402

SAMPLE_API_DIR = REPO_ROOT / "data" / "sample" / "api"
SAMPLE_SNAP_A = REPO_ROOT / "data" / "sample" / "snapA.json"
SAMPLE_SNAP_B = REPO_ROOT / "data" / "sample" / "snapB.json"


def test_diff_snapshots_detects_events_snapA_to_snapB():
    # Focus on curated sample snapshots
    assert SAMPLE_SNAP_A.exists() and SAMPLE_SNAP_B.exists()
    ts1, snap1 = mod.load_snapshot(SAMPLE_SNAP_A)
    ts2, snap2 = mod.load_snapshot(SAMPLE_SNAP_B)
    events = mod.diff_snapshots(snap1, snap2, ts2)

    by_bike = {}
    for e in events:
        by_bike.setdefault(e["bike_id"], []).append(e)

    # Bike 590066 is freestanding in A and at station in B -> two events
    evs = by_bike.get("590066")
    assert evs is not None and len(evs) == 2
    types = {e["event_type"] for e in evs}
    assert types == {"departed", "arrived"}
    dep = next(e for e in evs if e["event_type"] == "departed")
    arr = next(e for e in evs if e["event_type"] == "arrived")
    assert dep["station_name"] == "freestanding"
    assert arr["station_name"] == "Wrocław Leśnica, stacja kolejowa"


def test_save_events_to_db(tmp_path):
    ts1, snap1 = mod.load_snapshot(SAMPLE_SNAP_A)
    ts2, snap2 = mod.load_snapshot(SAMPLE_SNAP_B)
    events = mod.diff_snapshots(snap1, snap2, ts2)

    db_path = tmp_path / "test.db"
    mod.save_events_to_db(events, db_path)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT event_type, station_name FROM bike_status_changes WHERE bike_id=?",
            ("590066",),
        )
        rows = cur.fetchall()
        types = {r[0] for r in rows}
        assert types == {"departed", "arrived"}
    finally:
        conn.close()


def test_get_latest_files_sort_by_fetched_at(tmp_path):
    f1 = tmp_path / "bike_rides_a.json"
    f2 = tmp_path / "bike_rides_b.json"
    f3 = tmp_path / "bike_rides_c.json"
    f1.write_text(json.dumps({"_fetched_at": "2025-01-01T00:00:01"}), encoding="utf-8")
    f2.write_text(json.dumps({"_fetched_at": "2025-01-01T00:00:03"}), encoding="utf-8")
    f3.write_text(json.dumps({"_fetched_at": "2025-01-01T00:00:02"}), encoding="utf-8")
    latest = mod.get_latest_files(tmp_path, 2)
    assert [p.name for p in latest] == ["bike_rides_c.json", "bike_rides_b.json"]


def test_main_works_from_arbitrary_cwd(tmp_path):
    db_path = tmp_path / "test.db"
    data_dir = REPO_ROOT / "data" / "raw" / "api"
    os.makedirs(data_dir, exist_ok=True)
    shutil.copy2(SAMPLE_SNAP_A, data_dir / "bike_rides_a.json")
    shutil.copy2(SAMPLE_SNAP_B, data_dir / "bike_rides_b.json")
    cwd = Path.cwd()
    try:
        os.chdir(SRC_DIR)
        mod.main(data_dir=data_dir, db_path=db_path)
    finally:
        os.chdir(cwd)
    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM bike_status_changes"
        ).fetchone()[0]
        assert count > 0
    finally:
        conn.close()

def test_freestanding_electric_has_generic_station_name(tmp_path):
    # Prepare minimal snapshot with a freestanding electric bike
    payload = {
        "_fetched_at": "2025-01-01T00:00:00",
        "data": [
            {
                "cities": [
                    {
                        "places": [
                            {
                                "uid": "568267505",
                                "name": "BIKE 590066",
                                "placeType": "FREESTANDING_ELECTRIC_BIKE",
                                "geoCoords": {"lat": 51.14448, "lng": 16.854524},
                                "bikes": [
                                    {"number": 590066, "bikeType": "ELECTRIC_4G", "battery": 30}
                                ],
                            }
                        ]
                    }
                ]
            }
        ],
    }

    f = tmp_path / "sample.json"
    f.write_text(json.dumps(payload), encoding="utf-8")

    ts, bikes = mod.load_snapshot(f)
    assert ts == "2025-01-01T00:00:00"
    info = bikes.get("590066")
    assert info is not None
    assert info["station_name"] == "freestanding"
    assert info["station_id"] == "freestanding"


def test_snapA_freestanding_electric_station_name():
    assert SAMPLE_SNAP_A.exists()
    _, bikes = mod.load_snapshot(SAMPLE_SNAP_A)
    info = bikes.get("590066")
    assert info is not None, "Bike 590066 should be present in snapA"
    assert info["station_name"] == "freestanding"
    assert info["station_id"] == "freestanding"
