import argparse
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def _fetch_one(conn: sqlite3.Connection, sql: str, params: Tuple) -> int:
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return 0 if row is None or row[0] is None else row[0]


def _fetch_pairs(conn: sqlite3.Connection, sql: str, params: Tuple) -> List[Tuple]:
    cur = conn.execute(sql, params)
    return cur.fetchall()


def compute_metrics(conn: sqlite3.Connection, table: str, day: str) -> Dict:
    """
    Compute per-day metrics from the SQLite table.

    Parameters:
    - conn: open sqlite3 connection
    - table: table name to query (e.g., 'bike_rides' or 'sample_data')
    - day: date string 'YYYY-MM-DD' (based on start_time)
    """
    # Validate date
    try:
        _ = datetime.strptime(day, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError("day must be in YYYY-MM-DD format") from e

    # Total rides
    total_rides = _fetch_one(
        conn,
        f"SELECT COUNT(*) FROM {table} WHERE date(start_time)=date(?)",
        (day,),
    )

    # Histogram by start hour
    hist_rows = _fetch_pairs(
        conn,
        f"SELECT CAST(strftime('%H', start_time) AS INTEGER) AS h, COUNT(*) "
        f"FROM {table} WHERE date(start_time)=date(?) GROUP BY h ORDER BY h",
        (day,),
    )
    # Normalize keys to '0'..'23'
    bike_rentals_histogram = {str(int(h)): int(c) for h, c in hist_rows if h is not None}

    # Avg/total distance
    avg_distance = _fetch_one(
        conn,
        f"SELECT AVG(distance) FROM {table} WHERE date(start_time)=date(?)",
        (day,),
    )
    # Round to 3 decimals for km precision
    avg_distance = round(float(avg_distance), 3) if avg_distance else 0.0

    total_distance = _fetch_one(
        conn,
        f"SELECT SUM(distance) FROM {table} WHERE date(start_time)=date(?)",
        (day,),
    )
    total_distance = round(float(total_distance), 3) if total_distance else 0.0

    # Avg/total duration (duration in DB is in minutes)
    avg_duration = _fetch_one(
        conn,
        f"SELECT AVG(duration) FROM {table} WHERE date(start_time)=date(?)",
        (day,),
    )
    avg_duration = round(float(avg_duration), 2) if avg_duration else 0.0

    total_duration = _fetch_one(
        conn,
        f"SELECT SUM(duration) FROM {table} WHERE date(start_time)=date(?)",
        (day,),
    )
    total_duration = int(total_duration) if total_duration else 0

    # Round trips
    round_trips = _fetch_one(
        conn,
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE date(start_time)=date(?) AND start_station IS NOT NULL AND end_station IS NOT NULL AND start_station=end_station",
        (day,),
    )

    # Bikes left outside a station (end_station == 'Poza stacją')
    left_outside_station = _fetch_one(
        conn,
        f"SELECT COUNT(*) FROM {table} WHERE date(start_time)=date(?) AND end_station='Poza stacją'",
        (day,),
    )

    # Busiest stations (top 5 by total arrivals + departures)
    # SQLite doesn't support FULL OUTER JOIN; emulate via UNION of station sets
    busiest_rows = _fetch_pairs(
        conn,
        f"""
        WITH dep AS (
            SELECT start_station AS station, COUNT(*) AS departures
            FROM {table}
            WHERE date(start_time)=date(?) AND start_station IS NOT NULL
            GROUP BY start_station
        ), arr AS (
            SELECT end_station AS station, COUNT(*) AS arrivals
            FROM {table}
            WHERE date(start_time)=date(?) AND end_station IS NOT NULL
            GROUP BY end_station
        ),
        all_stations AS (
            SELECT station FROM dep
            UNION
            SELECT station FROM arr
        )
        SELECT s.station,
               COALESCE(arr.arrivals, 0) AS arrivals,
               COALESCE(dep.departures, 0) AS departures,
               COALESCE(arr.arrivals, 0) + COALESCE(dep.departures, 0) AS total
        FROM all_stations s
        LEFT JOIN dep ON dep.station = s.station
        LEFT JOIN arr ON arr.station = s.station
        ORDER BY total DESC, s.station ASC
        LIMIT 5
        """,
        (day, day),
    )
    busiest_stations_top5 = [
        {
            "station": r[0],
            "arrivals": int(r[1]),
            "departures": int(r[2]),
            "total": int(r[3]),
        }
        for r in busiest_rows
        if r and r[0] is not None
    ]

    # Top 5 routes by count
    route_rows = _fetch_pairs(
        conn,
        f"""
        SELECT start_station, end_station, COUNT(*) AS rides
        FROM {table}
        WHERE date(start_time)=date(?) AND start_station IS NOT NULL AND end_station IS NOT NULL
        GROUP BY start_station, end_station
        ORDER BY rides DESC, start_station ASC, end_station ASC
        LIMIT 5
        """,
        (day,),
    )
    top_routes_top5 = [
        {
            "start_station": r[0],
            "end_station": r[1],
            "rides": int(r[2]),
        }
        for r in route_rows
        if r and r[0] is not None and r[1] is not None
    ]

    return {
        "date": day,
        "total_rides": int(total_rides),
        "bike_rentals_histogram": bike_rentals_histogram,
        "avg_distance_km": avg_distance,
        "avg_duration_min": avg_duration,
        "total_distance_km": total_distance,
        "total_duration_min": total_duration,
        "round_trips": int(round_trips),
        "left_outside_station": int(left_outside_station),
        "busiest_stations_top5": busiest_stations_top5,
        "top_routes_top5": top_routes_top5,
    }


def list_dates_for_year(conn: sqlite3.Connection, table: str, year: int) -> List[str]:
    cur = conn.execute(
        f"SELECT date(start_time) AS d FROM {table} WHERE strftime('%Y', start_time)=? GROUP BY d ORDER BY d",
        (str(year),),
    )
    return [r[0] for r in cur.fetchall()]


def read_year_file(path: str) -> Dict:
    if not os.path.exists(path):
        return {"year": None, "days": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Accept both plain mapping and structured {year, days}
        if isinstance(data, dict) and "days" in data:
            year = data.get("year")
            days = data.get("days", {})
            return {"year": year, "days": days}
        elif isinstance(data, dict):
            return {"year": None, "days": data}
        else:
            return {"year": None, "days": {}}
    except Exception:
        return {"year": None, "days": {}}


def write_year_file(path: str, year: int, days: Dict[str, Dict]) -> None:
    ensure_dir(os.path.dirname(os.path.abspath(path)))
    payload = {"year": year, "days": days}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compute daily bike ride metrics and write JSON output.")
    parser.add_argument("--date", dest="day", default=None, help="Date YYYY-MM-DD (based on start_time)")
    parser.add_argument("--year", dest="year", type=int, default=None, help="Compute metrics for all dates in the given year")
    parser.add_argument(
        "--db",
        dest="db_path",
        default=os.path.join(repo_root(), "data", "processed", "bike_data.db"),
        help="Path to SQLite DB (default: data/processed/bike_data.db)",
    )
    parser.add_argument("--table", dest="table", default="bike_rides", help="Table name (default: bike_rides)")
    parser.add_argument(
        "--out",
        dest="out_path",
        default=None,
        help="Output JSON file path. For yearly mode defaults to data/processed/metrics/<year>.json; for single day defaults to data/processed/metrics/<year>.json (appending).",
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db_path)
    try:
        # Yearly rebuild mode
        if args.year is not None:
            dates = list_dates_for_year(conn, args.table, args.year)
            results: Dict[str, Dict] = {}
            for d in dates:
                results[d] = compute_metrics(conn, args.table, d)
            # Remove redundant 'date' inside each day's payload
            for d in list(results.keys()):
                if isinstance(results[d], dict):
                    results[d].pop("date", None)
            # Determine out path
            if args.out_path is None:
                out_dir = os.path.join(repo_root(), "data", "processed", "metrics")
                ensure_dir(out_dir)
                args.out_path = os.path.join(out_dir, f"{args.year}.json")
            else:
                ensure_dir(os.path.dirname(os.path.abspath(args.out_path)))
            write_year_file(args.out_path, args.year, results)
            print(f"Wrote yearly metrics for {args.year} to: {args.out_path}")
            return

        # Single day append/update into yearly file
        day = args.day or datetime.utcnow().strftime("%Y-%m-%d")
        year = int(day[:4])
        metrics = compute_metrics(conn, args.table, day)
        # default yearly file path
        if args.out_path is None:
            out_dir = os.path.join(repo_root(), "data", "processed", "metrics")
            ensure_dir(out_dir)
            args.out_path = os.path.join(out_dir, f"{year}.json")
        else:
            ensure_dir(os.path.dirname(os.path.abspath(args.out_path)))

        existing = read_year_file(args.out_path)
        days = existing.get("days", {})
        # store without redundant 'date'
        payload = dict(metrics)
        payload.pop("date", None)
        days[day] = payload
        write_year_file(args.out_path, year, days)
        print(f"Updated {day} in: {args.out_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
