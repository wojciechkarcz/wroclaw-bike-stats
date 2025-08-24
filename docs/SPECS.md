# Wroclaw Bike Stats — SPEC

## 0. Overview
Build a tiny web app that shows basic stats for city bike system in Wroclaw, Poland using its public API.
Stack: Python 3.10, SQLite, HTML/CSS/JS, static website, zero-auth, minimal deps.

## 1. Goals (MVP)
- Fetch bike rides data once per 24h and store inside sqlite database.
- Compute metrics for a single day (see point 4).
- Single static webpage with KPI cards + table updated once a day.
- Python script using jinja2 template to produce the final webpage with data.

## 2. Non-Goals (for now)
- No user accounts, no alerts, no web frameworks like Flask or Streamlit

## 3. Data Source
- Raw data fetched in .csv format.
- After fetching data is cleaned, transformed and stored in SQLite db.
- SQLite db schema (table name: bike_rides): uid INTEGER, bike_number TEXT, start_time TIMESTAMP, end_time TIMESTAMP, start_station TEXT, end_station TEXT, duration INTEGER, lat_start REAL, lon_start REAL, lat_end REAL, lon_end REAL, distance REAL

## 4. Metrics 
- All metrics are reffereing to the data from the last single day.
- Total number of bike rentals.
- Bike rentals by each hour a day (histogram).
- Avg. bike ride duration.
- Avg. bike ride distance.
- Top 5 bike routes.
- Top 5 busiest bike stations (sum of bike rentals and returns).
- Estimated daily revenue.

## 5. UI Requirements
- TBD

## 6. CLI / Scripts
- TBD

## 7. Directory Contract
- SQLite db location: `data/processed/bike_data.db`
- SQLite db location for bike status changes: `data/processed/bike_status.db`
- Raw data location: `data/raw/2025`
- Cleaned csv file location: `data/interim`
- File with bike stations name, lat/lon coordinates: `data/bike_stations.csv`
- Changelog location: `docs/CHANGELOG.md`
- Don't edit and modify files in these locations.

## 8. Quality & Constraints
- Keep deps minimal (requests, pandas/pyarrow, pydantic optional).
- 95% of logic in pure functions with unit tests.
- Lint with ruff; test with pytest; type hints encouraged.

## 9. Acceptance Tests (agent must satisfy)
- TBD

## 10. Future (parking lot)
- Map view, historical data from past years, bike station data, ML prediction algorithm.
- Historical data for every single day in the current year.