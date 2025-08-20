#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# === CONFIG ===
DATA_DIR = "/home/wojtek/dev/test/bike_rides_json_data"  # <- change this
URL = "https://api-gateway.nextbike.pl/api/maps/service/pl/locations"
TIMEZONE = "Europe/Warsaw"  # for local timestamp in filename

# === TIMEZONE HANDLING (stdlib only) ===
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    ZONE = ZoneInfo(TIMEZONE)
except Exception:
    ZONE = timezone.utc  # fallback if zoneinfo not available

def now_local_iso():
    return datetime.now(tz=ZONE).isoformat(timespec="seconds")

def now_local_for_filename():
    return datetime.now(tz=ZONE).strftime("%Y-%m-%d_%H_%M_%S")

def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
    with urlopen(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
        return json.loads(raw)

def main():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    try:
        payload = fetch_json(URL)
    except HTTPError as e:
        print(f"[ERROR] HTTP {e.code}: {e.reason}")
        return
    except URLError as e:
        print(f"[ERROR] URL error: {e.reason}")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected: {e}")
        return

    timestamp_iso = now_local_iso()

    # Attach the timestamp to the JSON. If it's not a dict, wrap it.
    if isinstance(payload, dict):
        payload["_fetched_at"] = timestamp_iso
    else:
        payload = {"_fetched_at": timestamp_iso, "data": payload}

    # Filename with local timestamp
    fname = f"bike_rides_{now_local_for_filename()}.json"
    fpath = Path(DATA_DIR) / fname

    # Write pretty but compact-ish JSON
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved {fpath}")

if __name__ == "__main__":
    main()
