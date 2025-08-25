#!/usr/bin/env python3
"""Fetch raw bike status data from the Nextbike API."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# === CONFIG ===
# Resolve repo root and default data directory (pathlib-based)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "raw" / "api"
URL = "https://api-gateway.nextbike.pl/api/maps/service/pl/locations"
TIMEZONE = "Europe/Warsaw"  # for local timestamp in filename

logger = logging.getLogger(__name__)

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
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko)"
                " Chrome/91.0.4472.124 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
        return json.loads(raw)

def main() -> Path | None:
    """Fetch the latest snapshot and save it under ``data/raw/api``.

    Returns the path to the saved file on success, otherwise ``None``.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Fetching bike status snapshot from %s", URL)
    try:
        payload = fetch_json(URL)
    except HTTPError as e:
        logger.error("HTTP %s: %s", e.code, e.reason)
        return None
    except URLError as e:
        logger.error("URL error: %s", e.reason)
        return None
    except Exception as e:  # pragma: no cover - unexpected failures
        logger.error("Unexpected error: %s", e)
        return None

    timestamp_iso = now_local_iso()

    if isinstance(payload, dict):
        payload["_fetched_at"] = timestamp_iso
    else:
        payload = {"_fetched_at": timestamp_iso, "data": payload}

    fname = f"bike_rides_{now_local_for_filename()}.json"
    fpath = DATA_DIR / fname
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("Saved snapshot to %s", fpath)
    return fpath


if __name__ == "__main__":
    main()
