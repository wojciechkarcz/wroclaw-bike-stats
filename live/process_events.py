#!/usr/bin/env python3
"""Generate live_events.json for the live map page.

Compares the two most recent Nextbike API snapshots (raw JSON files) and
writes a single JSON file with all arrival/departure events detected between
them. The file is everything the frontend (live/index.html) needs.

Meant to be run from cron every minute, right after the snapshot downloader:

    * * * * * cd /path/to/wroclaw-bike-stats && python3 live/process_events.py

The diff logic is reused from src/bike_status_changes.py, so the events in
the output file are exactly the same records that land in bike_status.db.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.bike_status_changes import (  # noqa: E402
    diff_snapshots,
    get_latest_files,
    load_snapshot,
)

DEFAULT_DATA_DIR = REPO_ROOT / "data" / "raw" / "api"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "live_events.json"


def build_payload(data_dir: Path) -> dict:
    files = get_latest_files(data_dir, 2)
    if len(files) < 2:
        raise SystemExit(f"Need at least 2 snapshot files in {data_dir}")

    ts_prev, prev = load_snapshot(files[0])
    ts_curr, curr = load_snapshot(files[1])
    events = diff_snapshots(prev, curr, ts_curr)

    return {
        "generated_at": ts_curr,
        "previous_snapshot_at": ts_prev,
        "interval_seconds": 60,
        "event_count": len(events),
        "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory with raw bike_rides_*.json snapshots (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the result (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    payload = build_payload(args.data_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    tmp.replace(args.output)  # atomic swap so the frontend never sees a partial file

    print(
        f"Wrote {payload['event_count']} events "
        f"({payload['previous_snapshot_at']} -> {payload['generated_at']}) "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
