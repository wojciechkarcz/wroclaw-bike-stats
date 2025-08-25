"""Run the full ETL pipeline for bike status data."""

from __future__ import annotations

import logging
from datetime import datetime

import bike_status_changes  # noqa: E402
import fetch_nextbike  # noqa: E402
from logging_config import setup_logging  # noqa: E402


def main() -> None:
    setup_logging()
    logger = logging.getLogger("pipeline")
    start = datetime.utcnow().isoformat()
    logger.info("ETL pipeline started", extra={"start": start})

    snapshot_path = fetch_nextbike.main()
    if snapshot_path is None:
        logger.error("Snapshot fetch failed; aborting")
        return
    logger.info("Fetched snapshot %s", snapshot_path)

    result = bike_status_changes.main()
    files = ", ".join(p.name for p in result.get("files", []))
    logger.info(
        "Processed snapshots: %s; added %d records",
        files,
        result.get("events", 0),
    )
    end = datetime.utcnow().isoformat()
    logger.info("ETL pipeline finished", extra={"end": end})


if __name__ == "__main__":
    main()
