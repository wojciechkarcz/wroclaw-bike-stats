#!/usr/bin/env python3
"""Local end-to-end demo of the live map, no server needed.

Simulates the production setup: every N seconds a "new" API snapshot appears
(taken from live/test_snapshots/*.json.gz), process_events.py regenerates
live_events.json, and a local HTTP server serves the live/ folder.

Usage:
    python3 live/simulate.py                 # new snapshot every 60 s, like prod
    python3 live/simulate.py --interval 15   # faster, for impatient testing

Then open http://localhost:8000 in your browser.
"""
from __future__ import annotations

import argparse
import functools
import gzip
import http.server
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

LIVE_DIR = Path(__file__).resolve().parent
SNAPSHOTS_DIR = LIVE_DIR / "test_snapshots"
SIM_RAW_DIR = LIVE_DIR / ".sim_raw"
PROCESS_SCRIPT = LIVE_DIR / "process_events.py"


def unpack(src: Path, dest_dir: Path) -> Path:
    dest = dest_dir / src.name.removesuffix(".gz")
    with gzip.open(src, "rb") as f_in, open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return dest


def run_processor() -> None:
    subprocess.run(
        [sys.executable, str(PROCESS_SCRIPT), "--data-dir", str(SIM_RAW_DIR)],
        check=True,
    )


def feeder(interval: float) -> None:
    snapshots = sorted(SNAPSHOTS_DIR.glob("*.json.gz"))
    if len(snapshots) < 2:
        raise SystemExit(f"Need at least 2 *.json.gz files in {SNAPSHOTS_DIR}")

    while True:
        # Fresh start: first two snapshots give the first batch of events.
        shutil.rmtree(SIM_RAW_DIR, ignore_errors=True)
        SIM_RAW_DIR.mkdir(parents=True)
        unpack(snapshots[0], SIM_RAW_DIR)
        unpack(snapshots[1], SIM_RAW_DIR)
        print(f"[sim] snapshots 1-2 -> processing")
        run_processor()
        time.sleep(interval)

        for i, snap in enumerate(snapshots[2:], start=3):
            unpack(snap, SIM_RAW_DIR)
            print(f"[sim] snapshot {i} arrived -> processing")
            run_processor()
            time.sleep(interval)

        print("[sim] ran out of snapshots, looping from the start")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=60,
                        help="Seconds between simulated snapshots (default: 60)")
    parser.add_argument("--port", type=int, default=8000,
                        help="HTTP port for the demo page (default: 8000)")
    args = parser.parse_args()

    threading.Thread(target=feeder, args=(args.interval,), daemon=True).start()

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(LIVE_DIR)
    )
    print(f"Serving the live map on http://localhost:{args.port} (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
