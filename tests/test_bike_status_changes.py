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

SAMPLE_DIR = REPO_ROOT / "data" / "sample" / "api"


def test_diff_snapshots_detects_events():
    files = sorted(SAMPLE_DIR.glob("bike_rides_*.json"))[:2]
    ts1, snap1 = mod.load_snapshot(files[0])
    ts2, snap2 = mod.load_snapshot(files[1])
    events = mod.diff_snapshots(snap1, snap2, ts2)

    by_bike = {}
    for e in events:
        by_bike.setdefault(e["bike_id"], []).append(e)

    # bike present in first snapshot only -> departed from freestanding
    evs = by_bike.get("591207")
    assert evs and evs[0]["event_type"] == "departed"
    assert evs[0]["station_name"] == "freestanding"

    # bike present in second snapshot only -> arrived to a station
    evs = by_bike.get("590520")
    assert evs and evs[0]["event_type"] == "arrived"
    assert evs[0]["station_name"] == "Żmigrodzka / Broniewskiego"

    # bike moved between locations -> two events
    evs = by_bike.get("591149")
    types = {e["event_type"] for e in evs}
    assert types == {"departed", "arrived"}
    dep = next(e for e in evs if e["event_type"] == "departed")
    arr = next(e for e in evs if e["event_type"] == "arrived")
    assert dep["station_name"] == "Na Grobli (PWr - Geocentrum)"
    assert arr["station_name"] == "freestanding"


def test_save_events_to_db(tmp_path):
    files = sorted(SAMPLE_DIR.glob("bike_rides_*.json"))[:2]
    ts1, snap1 = mod.load_snapshot(files[0])
    ts2, snap2 = mod.load_snapshot(files[1])
    events = mod.diff_snapshots(snap1, snap2, ts2)

    db_path = tmp_path / "test.db"
    mod.save_events_to_db(events, db_path)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT event_type, station_name FROM bike_status_changes WHERE bike_id=?",
            ("591149",),
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
    cwd = Path.cwd()
    try:
        os.chdir(SRC_DIR)
        mod.main(db_path=db_path)
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
