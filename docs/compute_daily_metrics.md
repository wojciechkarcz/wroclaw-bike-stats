# Compute Daily Metrics

The `compute_daily_metrics.py` script calculates daily bike ride metrics from SQLite and stores results in a single yearly JSON file. It supports appending a single day (for daily runs) and rebuilding a whole year directly from the database.

## Summary
- Input DB: `data/processed/bike_data.db` (default)
- Default table: `bike_rides` (accepts custom table e.g., `sample_data`)
- Output JSON: `data/processed/metrics/<year>.json`
- Date reference: uses `start_time` as the ride date
- Duration unit: minutes

## Usage
Run the script via Python:

```bash
python src/compute_daily_metrics.py [options]
```

### Common options
- `--db <path>`: Path to SQLite DB (default: `data/processed/bike_data.db`).
- `--table <name>`: Table name (default: `bike_rides`).
- `--out <path>`: Output JSON file path. By default the script writes to `data/processed/metrics/<year>.json`.

### Modes
1) Append or update a single day in the yearly file (use this for daily runs):

```bash
python src/compute_daily_metrics.py --date 2025-04-07
```

- Determines `<year>` from the date and updates `data/processed/metrics/2025.json`.
- If the yearly file does not exist, it is created.

2) Rebuild a whole year from the DB (loads all available dates in that year):

```bash
python src/compute_daily_metrics.py --year 2025
```

- Scans the DB for distinct `date(start_time)` within 2025 and computes metrics for each date.
- Writes all results to `data/processed/metrics/2025.json` (overwrites existing file).

## Output format
A single yearly JSON file containing all days:

```json
{
  "year": 2025,
  "days": {
    "2025-04-07": {
      "total_rides": 123,
      "bike_rentals_histogram": {"0": 2, "1": 1, "2": 0, "3": 0},
      "avg_distance_km": 2.175,
      "total_distance_km": 8.7,
      "avg_duration_min": 19.25,
      "total_duration_min": 77,
      "round_trips": 10,
      "left_outside_station": 3,
      "busiest_stations_top5": [{"station": "Rynek", "arrivals": 12, "departures": 15, "total": 27}],
      "top_routes_top5": [{"start_station": "A", "end_station": "B", "rides": 9}]
    }
  }
}
```

Notes:
- Keys inside `days` are ISO dates derived from `start_time` (`YYYY-MM-DD`).
- The script stores only the per-day payload under `days[<date>]` and keeps the top-level `year` for convenience.

## Examples
- Append metrics for the latest day (UTC today):

```bash
python src/compute_daily_metrics.py --date $(date -u +%F)
```

- Append metrics using a custom DB and table:

```bash
python src/compute_daily_metrics.py \
  --date 2025-04-07 \
  --db data/processed/bike_data.db \
  --table sample_data
```

- Rebuild 2025 metrics and write to a custom file:

```bash
python src/compute_daily_metrics.py --year 2025 --out data/processed/metrics/bikes-2025.json
```

## Implementation details
- Global filter: exclude rides with `duration <= 2` minutes from all metrics.
- Busiest stations: top 5 by total arrivals + departures per station; excludes station name `Poza stacją`.
- Top routes: top 5 by ride count grouped by `(start_station, end_station)`; excludes round trips (`start_station = end_station`) and any route where either end is `Poza stacją`.
- Histogram: number of rides grouped by the hour of `start_time`.
- Distance is expected in kilometers in the DB; duration is expected in minutes.

## Directory contract
- Input DB: `data/processed/bike_data.db`
- Output JSON: `data/processed/metrics/<year>.json`
- These paths follow the project SPEC (`docs/SPECS.md`).
