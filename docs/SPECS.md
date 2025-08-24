# Wroclaw Bike Stats — SPEC

## 0. Overview
Build a tiny web app that shows basic stats for the city bike system in Wroclaw, Poland.  
Stack: Python 3.10, SQLite, HTML/CSS/JS, static website, zero-auth, minimal deps.

## 1. Goals (MVP)
- Fetch bike rides data once per 24h and store in SQLite (`bike_data.db`).
- Fetch near real-time bike/station status data via official API and store in SQLite (`bike_status.db`).
- Compute metrics for a single day (see point 4).
- Single static webpage with KPI cards + table updated once a day.
- Python script using Jinja2 template to produce the final webpage with data.

## 2. Non-Goals (for now)
- No user accounts, no alerts, no web frameworks like Flask or Streamlit.

## 3. Data Sources
### 3.1. Daily rides data
- Source: raw daily `.csv` file with all rides.
- ETL script: `src/data_load_sqlite.py`
- Database: `data/processed/bike_data.db`
- Schema (table: `bike_rides`):
uid INTEGER,  
bike_number TEXT,  
start_time TIMESTAMP,  
end_time TIMESTAMP,  
start_station TEXT,  
end_station TEXT,  
duration INTEGER,  
lat_start REAL,  
lon_start REAL,  
lat_end REAL,  
lon_end REAL,  
distance REAL

### 3.2. Real-time bike status data
- Source: official Nextbike API (JSON).
- Fetch script: `src/fetch_nextbike.py` (stores raw JSON responses).
- Transform script: `src/bike_status_changes.py` (parses events into SQLite).
- Database: `data/processed/bike_status.db`
- Schema (table: `bike_status_changes`):
uid INTEGER PRIMARY KEY AUTOINCREMENT,  
timestamp TEXT,  
bike_id TEXT,  
event_type TEXT,  
station_name TEXT,  
station_id TEXT,  
lat REAL,  
lon REAL,  
bike_type TEXT,  
battery REAL

## 4. Metrics
(Currently based on daily rides data; integration with real-time status TBD)
- Total number of bike rentals.
- Bike rentals by each hour a day (histogram).
- Avg. bike ride duration.
- Avg. bike ride distance.
- Top 5 bike routes.
- Top 5 busiest bike stations (sum of bike rentals and returns).
- Estimated daily revenue.

## 5. UI Requirements
- Minimal static HTML/CSS/JS (templated via Jinja2).
- Show KPI cards and tables for one selected day.
- Future: possible integration of real-time status visualizations.

## 6. CLI / Scripts
- `src/data_load_sqlite.py` → ETL daily rides (CSV → SQLite).
- `src/fetch_nextbike.py` → fetch raw station/bike JSON snapshots.
- `src/bike_status_changes.py` → process snapshots → `bike_status_changes` table.
- Report generator script (TBD) → produce final static HTML report.

## 7. Directory Contract
- Daily rides DB: `data/processed/bike_data.db`
- Bike status DB: `data/processed/bike_status.db`
- Raw data: `data/raw/2025`
- Interim cleaned CSV: `data/interim`
- Bike stations reference file: `data/bike_stations.csv`    
- Don’t edit or modify files in these locations manually.

## 8. Quality & Constraints
- Keep deps minimal (`requests`, `pandas`/`pyarrow`; `pydantic` optional).
- 95% of logic in pure functions with unit tests.
- Lint with `ruff`; test with `pytest`; type hints encouraged.

## 9. Acceptance Tests (agent must satisfy)
- TBD

## 10. Future (parking lot)
- Define how daily ride data and real-time status data complement each other.
- Map view of stations and bike movements.
- Historical data from past years.
- ML prediction algorithms (demand, redistribution).
- Revenue analysis at weekly/monthly level.
