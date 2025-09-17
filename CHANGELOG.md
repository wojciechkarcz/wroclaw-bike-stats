## #16 - Web app for displaying bike rides data (2025-09-08)

- Scaffold static web UI under `/web` with Single Day and Date Range views.
- Line charts via Chart.js (tooltips, rotated x ticks, Y from 0); SVG fallback kept.
- Date validation and snapping to available dates; ensure `end >= start` with bound updates.
- Single Day: histogram with axes and value-on-hover; busiest stations and top routes as tables; default to latest date.
- Date Range: stacked daily metric charts; averaged hourly histogram; busiest stations and top routes as tables; default last 7 days.
- New: adaptive x-axis tick density for Date Range charts based on container width.
- Data served from `/web/data/rides.json` copied from processed metrics.

Key decisions/assumptions:
- Use Chart.js for richer interactivity; keep minimal SVG fallback.
- Serve `web/` as site root so `/data/rides.json` is reachable.

## #15 - Script for calculating general metrics (2025-09-08)

- Summary: Implement daily metrics CLI that computes per-day metrics and writes yearly JSON aggregates; add tests; introduce minimal HTML viewer; apply filters/exclusions and performance improvements; update bike station coordinates data.
- Decisions/Assumptions: Durations measured in minutes; histogram buckets by start hour; script reads from any SQLite table (uses `sample_data` for tests); yearly mode appends/merges by date to avoid full rewrites; outputs under `data/processed/metrics/<year>.json`.

## #13 - Add bike rides CLI (2025-08-25)

- Feat: consolidate CSV download and loading commands into `bike_rides_cli.py`.
- Chore: remove older standalone downloader scripts.
- Docs: add usage guide for `bike_rides_cli.py`.

## #12 - Add unified pipeline and logging (2025-08-25)

- Feat: add `src/pipeline.py` orchestrating fetch and status change processing.
- Feat: central logging with rotating file handler and start/end markers.
- Chore: replace separate cron jobs with single pipeline invocation.

## #11 - Wrong station name for freestanding electric bikes (2025-08-24)

- Fix: normalize `station_name`/`station_id` to `freestanding` for any `placeType` starting with `FREESTANDING`.
- Parse: support both `bikes` objects and `bikeNumbers` lists within places.
- Tests: add focused tests using `data/sample/snapA.json`, `data/sample/snapB.json`, and a freestanding-electric case.

Key decisions/assumptions:
- Broad match on `placeType` to handle variations.
- Prefer generic naming for freestanding entries.

## Finish raw data loading script (2025-08-19)

- Validated `src/data_load_sqlite.py` downloads the latest CSV, transforms data, and stores results in SQLite while saving cleaned CSV output.
- Ensured data paths comply with `docs/SPECS.md`.
- Added a regression test covering the script's end-to-end flow.

## Load all data to SQLite db (2025-08-19)

- Added `load_to_sqlite.py` to load all CSV files from `data/raw/2025` into SQLite using the same process as `src/data_load_sqlite.py`.
- Reused shared transformations to keep ingestion consistent across datasets.

## Basic project setup (2025-08-18)

- Established initial project structure and tooling foundation.
