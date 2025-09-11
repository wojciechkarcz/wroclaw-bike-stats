import argparse
import os
import shutil
import sqlite3
import sys
import datetime as dt
from typing import Optional, Tuple, List

from geopy.distance import geodesic


def repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def compute_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
    try:
        a1 = (float(lat1), float(lon1))
        a2 = (float(lat2), float(lon2))
    except (TypeError, ValueError):
        return None
    try:
        return round(geodesic(a1, a2).km, 3)
    except Exception:
        return None


def backup_db(db_path: str) -> str:
    base_dir = os.path.dirname(db_path)
    backup_dir = os.path.join(base_dir, "backups")
    ensure_dir(backup_dir)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{os.path.splitext(os.path.basename(db_path))[0]}_{ts}.bak.db"
    dst = os.path.join(backup_dir, name)
    shutil.copy2(db_path, dst)
    return dst


def fetch_rows_to_update(conn: sqlite3.Connection, table: str) -> List[Tuple[int, float, float, float, float]]:
    sql = f"""
        SELECT uid, lat_start, lon_start, lat_end, lon_end
        FROM {table}
        WHERE distance IS NULL
          AND lat_start IS NOT NULL AND lon_start IS NOT NULL
          AND lat_end IS NOT NULL AND lon_end IS NOT NULL
    """
    cur = conn.execute(sql)
    return cur.fetchall()


def backfill_distances(db_path: str, table: str = "bike_rides", *, dry_run: bool = False, do_backup: bool = True) -> int:
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)

    if do_backup and not dry_run:
        backup = backup_db(db_path)
        print(f"Created backup: {backup}")

    conn = sqlite3.connect(db_path)
    try:
        rows = fetch_rows_to_update(conn, table)
        print(f"Rows with NULL distance and valid coords: {len(rows)}")
        updates: List[Tuple[float, int]] = []
        for uid, lat1, lon1, lat2, lon2 in rows:
            d = compute_distance_km(lat1, lon1, lat2, lon2)
            if d is not None:
                updates.append((d, uid))

        print(f"Will update {len(updates)} rows")

        if dry_run or not updates:
            return len(updates)

        with conn:
            conn.executemany(
                f"UPDATE {table} SET distance = ? WHERE uid = ?",
                updates,
            )
        return len(updates)
    finally:
        conn.close()


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill NULL distances in SQLite DB")
    parser.add_argument("--db", default=os.path.join(repo_root(), "data", "processed", "bike_data.db"), help="Path to SQLite DB")
    parser.add_argument("--table", default="bike_rides", help="Table name")
    parser.add_argument("--dry-run", action="store_true", help="Print how many rows would be updated, without changing the DB")
    parser.add_argument("--no-backup", action="store_true", help="Do not create a backup before updating")
    args = parser.parse_args(argv)

    updated = backfill_distances(args.db, args.table, dry_run=args.dry_run, do_backup=not args.no_backup)
    print(f"Updated rows: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

