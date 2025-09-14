# 🚲 Wrocław Bike Stats

Wrocław Bike Stats is a “data sandbox project”: an ongoing, safe playground to experiment with the full data lifecycle — from data extraction and transformation through storage and aggregation to a simple web UI. It’s designed to test tools, patterns, and agentic workflows on real public data from the Wrocław city bike system.

Majority of the code is generated using Codex CLI to explore agentic development for data projects. My setup and conventions are documented in `AGENTS.md`.

Live app: http://wrocbike.tojest.dev

## Why Wrocław?

Wrocław is currently the only city in Poland with easily accessible open data for the public bike rental system. This makes it ideal for an open, continuously updated analytics sandbox.

All open data on Wrocław city bike system can be found [here](https://opendata.cui.wroclaw.pl/dataset?tags=rowery).

## Architecture (current state)

- Data extraction (daily rides): `src/bike_rides_cli.py` downloads CSVs from the city open-data portal, transforms them, and loads to SQLite at `data/processed/bike_data.db`.
- Transformation: station coordinates are merged into each ride; types are normalized; distances are computed in kilometers.
- Aggregation (daily metrics): `src/compute_daily_metrics.py` writes per-day results into `data/processed/metrics/<year>.json` (append or yearly rebuild).
- Web app: a static HTML/CSS/JS site under `web/` that reads JSON metrics from `web/data/rides.json` (served at `/data/rides.json`) and displays single-day and date‑range views with charts and tables.
- Real-time status (separate track): snapshots from the Nextbike API are saved to `data/raw/api` by `src/fetch_nextbike.py`, and station arrival/departure events are derived into `data/processed/bike_status.db` by `src/bike_status_changes.py`. This is not yet integrated into the web UI metrics.

Deployment: everything runs on my VPS ([Mikrus](http://mikr.us)). The web app is served as a simple static site via nginx. No server-side app — just static assets reading JSON files.

Directory contract and details are specified in `docs/SPECS.md`.

## Data Ingestion Tracks

There are two independent, complementary tracks for getting data into the project:

### Historical rides (CSV, open data, ~2‑day delay)
- Source: daily CSVs published on the city open‑data portal.
- Pipeline: `src/bike_rides_cli.py` → transform → SQLite `data/processed/bike_data.db`.
- Nature: finalized trips with a publication lag (~2 days). Best for accurate historical analytics and daily metrics.
- Enrichment: station coordinates are merged; distances (km) and durations (min) are computed/normalized during transform.

### Near real‑time status (API snapshots, every minute)
- Source: official Nextbike API; snapshots fetched by `src/fetch_nextbike.py` and saved under `data/raw/api/`.
- Derivation: `src/bike_status_changes.py` compares the two latest snapshots and records events in `data/processed/bike_status.db`.
- Events:
  - Bike departed — a bike present at a station in the previous snapshot disappears (or changes station) in the current snapshot.
  - Bike arrived — a bike appears at a station in the current snapshot that wasn’t at that station previously.
- Notes: freestanding bikes (not docked at a station) are treated as `freestanding`. Snapshots may include transient fluctuations; the DB is an append‑only log of inferred arrivals/departures. This track is currently separate from the daily metrics UI.

## CLI reference

All key scripts can be run with Python 3.10+ from the repo root. Paths follow the directory contract in `docs/SPECS.md`.

### Bike rides ETL — download, transform, load

Script: `src/bike_rides_cli.py`
Docs: [bike_rides.cli.md](https://github.com/wojciechkarcz/wroclaw-bike-stats/blob/main/docs/bike_rides_cli.md)
Usage:
```
python src/bike_rides_cli.py <latest|date|all|load-folder> [--no-transform] [--no-sqlite]
```

Examples:
```
python src/bike_rides_cli.py latest
python src/bike_rides_cli.py date 2025-08-20
python src/bike_rides_cli.py load-folder data/raw/2025
```

### Compute daily metrics — JSON for web UI

Script: `src/compute_daily_metrics.py`
Docs: [compute_daily_metrics.md](https://github.com/wojciechkarcz/wroclaw-bike-stats/blob/main/docs/compute_daily_metrics.md)
Common options: `--db`, `--table`, `--out`, `--latest`, `--year`

Examples:
```
python src/compute_daily_metrics.py --latest
python src/compute_daily_metrics.py --year 2025
```
Output: `data/processed/metrics/<year>.json`

### Backfill missing distances — fix historical rows

Script: `src/backfill_distance.py`
Docs: [backfill_distance.md](https://github.com/wojciechkarcz/wroclaw-bike-stats/blob/main/docs/backfill_distance.md)

Commands:
```
python src/backfill_distance.py --dry-run
python src/backfill_distance.py
```

### Real-time snapshots → status changes (separate track)

Fetch latest snapshot (saves under `data/raw/api/`):
```
python src/fetch_nextbike.py
```

Derive arrival/departure events (writes to `data/processed/bike_status.db`):
```
python src/bike_status_changes.py
```

Simple pipeline runner (fetch + derive):
```
python src/pipeline.py
```

## Usage

The whole code runs on my VPS as a regular cron job:
```
58 19 * * * /usr/bin/python3 /path/to/wroclaw-bike-stats/src/bike_rides_cli.py latest >> /path/to/wroclaw-bike-stats/temp/cron_fetch_csv.log > 2>&1
00 20 * * * /usr/bin/python3 /path/to/wroclaw-bike-stats/src/compute_daily_metrics.py --latest --out /path/to/wroclaw-bike-stats/web/data/rides.json
```


## Project overview and goals

- Learn and practice end‑to‑end data engineering and analytics on real public data
- Keep the stack minimal: Python, SQLite, static web, few deps
- Evolve towards richer analytics (e.g., ML) without rushing complexity
