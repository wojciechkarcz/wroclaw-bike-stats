# Backfill: Recompute Missing Distances

This utility recomputes `distance` (in kilometers) for bike ride rows in SQLite where `distance` is `NULL` but coordinates are present. It is safe, idempotent, and creates a timestamped backup by default.

## When to Use
- Historical ETL runs produced rows with `NULL` distance due to malformed station coordinates (e.g., duplicate header rows in the stations CSV). After fixing the transform, use this backfill to fill in distances for existing data without reloading.

## What It Does
- Selects rows from `bike_rides` with `distance IS NULL` and non-null `lat_start`, `lon_start`, `lat_end`, `lon_end`.
- Computes geodesic distance (via `geopy.distance.geodesic`) and rounds to 3 decimals.
- Updates only those rows; leaves others unchanged.
- Creates a backup copy of the DB in `data/processed/backups/` before making changes (can be disabled).

## CLI
- Location: `src/backfill_distance.py`
- Defaults:
  - `--db`: `data/processed/bike_data.db`
  - `--table`: `bike_rides`
  - Backup enabled by default

### Commands
- Preview changes (no DB writes):
  - `python3 src/backfill_distance.py --dry-run`
- Backfill with backup:
  - `python3 src/backfill_distance.py`
- Backfill without backup (not recommended):
  - `python3 src/backfill_distance.py --no-backup`
- Custom DB/table:
  - `python3 src/backfill_distance.py --db path/to.db --table my_table`

## Notes
- Rows with missing coordinates will remain `NULL` by design.
- The operation is idempotent; subsequent runs only affect newly added rows with `NULL` distance.
- Dependencies: uses `geopy` (already in `requirements.txt`).

## Related Fix
- The ETL transform now coerces station coordinates to numeric and drops accidental embedded headers in the stations CSV, preventing future `NULL` distances at load time.
