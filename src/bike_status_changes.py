#!/usr/bin/env python3
"""Detect bike status changes between the latest API snapshots.

This script compares the two most recent JSON files downloaded from the
Nextbike API and records any bike arrivals or departures into an SQLite
database table called ``bike_status_changes``.

The database path defaults to ``data/processed/bike_data.db`` as defined in
``docs/SPECS.md``.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# Resolve repo root so defaults work regardless of CWD
REPO_ROOT = Path(__file__).resolve().parents[1]
# Default locations following project specs
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "sample" / "api"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "processed" / "bike_data.db"


def load_snapshot(path: Path) -> Tuple[str, Dict[str, Dict[str, object]]]:
    """Load single snapshot returning timestamp and mapping of bikes.

    Returns
    -------
    tuple
        ``(timestamp_iso, bikes)`` where ``bikes`` maps ``bike_id`` to info
        about station and bike metadata.
    """
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    timestamp = payload.get("_fetched_at")
    places = payload["data"][0]["cities"][0]["places"]
    bikes: Dict[str, Dict[str, object]] = {}

    for place in places:
        bikes_list = place.get("bikes") or []
        if not bikes_list:
            continue
        place_type = place.get("placeType")
        if place_type == "FREESTANDING_BIKE":
            station_name = "freestanding"
            station_id = "freestanding"
        else:
            station_name = place.get("name")
            station_id = str(place.get("uid"))
        lat = place["geoCoords"]["lat"]
        lon = place["geoCoords"]["lng"]
        for bike in bikes_list:
            bike_id = str(bike["number"])
            bike_type_field = str(bike.get("bikeType", "")).upper()
            bike_type = "electric" if bike_type_field.startswith("ELECTRIC") else "standard"
            bikes[bike_id] = {
                "station_name": station_name,
                "station_id": station_id,
                "lat": lat,
                "lon": lon,
                "bike_type": bike_type,
                "battery": bike.get("battery"),
            }
    return timestamp, bikes


def get_latest_files(data_dir: Path, count: int = 2) -> List[Path]:
    """Return ``count`` most recent JSON files in ``data_dir``.

    Sorting is based on the ``_fetched_at`` timestamp stored inside each
    snapshot instead of the filename.
    """
    meta = []
    for path in data_dir.glob("bike_rides_*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            meta.append((payload.get("_fetched_at", ""), path))
        except (OSError, json.JSONDecodeError):
            continue
    meta.sort(key=lambda x: x[0])
    return [p for _, p in meta[-count:]]


def diff_snapshots(
    prev: Dict[str, Dict[str, object]],
    curr: Dict[str, Dict[str, object]],
    timestamp: str,
) -> List[Dict[str, object]]:
    """Compute arrival/departure events between two snapshots."""
    events: List[Dict[str, object]] = []

    # Departures and moves
    for bike_id, info in prev.items():
        if bike_id not in curr:
            events.append(
                {
                    "timestamp": timestamp,
                    "bike_id": bike_id,
                    "event_type": "departed",
                    **info,
                }
            )
        else:
            new_info = curr[bike_id]
            if info["station_id"] != new_info["station_id"]:
                events.append(
                    {
                        "timestamp": timestamp,
                        "bike_id": bike_id,
                        "event_type": "departed",
                        **info,
                    }
                )
                events.append(
                    {
                        "timestamp": timestamp,
                        "bike_id": bike_id,
                        "event_type": "arrived",
                        **new_info,
                    }
                )

    # Arrivals (new bikes)
    for bike_id, info in curr.items():
        if bike_id not in prev:
            events.append(
                {
                    "timestamp": timestamp,
                    "bike_id": bike_id,
                    "event_type": "arrived",
                    **info,
                }
            )

    return events


def save_events_to_db(events: Iterable[Dict[str, object]], db_path: Path) -> None:
    """Insert events into SQLite, creating table if needed."""
    if not events:
        return
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bike_status_changes (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                bike_id TEXT,
                event_type TEXT,
                station_name TEXT,
                station_id TEXT,
                lat REAL,
                lon REAL,
                bike_type TEXT,
                battery REAL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO bike_status_changes (
                timestamp, bike_id, event_type, station_name, station_id,
                lat, lon, bike_type, battery
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    e["timestamp"],
                    e["bike_id"],
                    e["event_type"],
                    e["station_name"],
                    e["station_id"],
                    e["lat"],
                    e["lon"],
                    e["bike_type"],
                    e["battery"],
                )
                for e in events
            ],
        )
        conn.commit()
    finally:
        conn.close()


def main(data_dir: Path = DEFAULT_DATA_DIR, db_path: Path = DEFAULT_DB_PATH) -> None:
    files = get_latest_files(data_dir, 2)
    if len(files) < 2:
        print("[WARN] Not enough JSON files to compare")
        return
    ts_prev, prev = load_snapshot(files[0])
    ts_curr, curr = load_snapshot(files[1])
    events = diff_snapshots(prev, curr, ts_curr)
    save_events_to_db(events, db_path)
    print(f"[OK] Recorded {len(events)} events")


if __name__ == "__main__":
    main()
