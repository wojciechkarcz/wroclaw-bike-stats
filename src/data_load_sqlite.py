import os
import re
import sqlite3
import datetime as dt
from urllib.parse import urljoin, urlparse

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


URL = 'https://opendata.cui.wroclaw.pl/dataset/wrmprzejazdy_data/resource_history/c737af89-bcf7-4f7d-8bbc-4a0946d7006e'


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make_session():
    s = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return s


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def extract_dt_from_filename(name: str):
    """Extract datetime from filenames like Historia_przejazdow_2025-8-18_18_29_14.csv."""
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})(?:_(\d{1,2})_(\d{1,2})_(\d{1,2}))?', name)
    if not m:
        return None
    y, mo, d, hh, mm, ss = m.groups()
    try:
        if hh is not None:
            return dt.datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss))
        return dt.datetime(int(y), int(mo), int(d))
    except ValueError:
        return None


def get_all_csv_urls(page_url: str, session: requests.Session):
    resp = session.get(page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    anchors = soup.find_all('a', class_='heading')
    hrefs = [a.get('href') for a in anchors if a.get('href')]
    urls = [urljoin(page_url, h) for h in hrefs]
    return [u for u in urls if u.lower().endswith('.csv')]


def pick_latest_csv(csv_urls):
    dated = []
    for u in csv_urls:
        fn = os.path.basename(urlparse(u).path)
        dtv = extract_dt_from_filename(fn)
        if dtv is not None:
            dated.append((dtv, u, fn))
    if not dated:
        return None, None
    dated.sort(key=lambda x: x[0], reverse=True)
    _, url, filename = dated[0]
    return url, filename


def download_file(url: str, out_dir: str, session: requests.Session):
    ensure_dir(out_dir)
    filename = os.path.basename(urlparse(url).path)
    path = os.path.join(out_dir, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return path


def distance_km(row):
    a1 = (row['lat_start'], row['lon_start'])
    a2 = (row['lat_end'], row['lon_end'])
    try:
        if np.isnan(a1[0]) or np.isnan(a1[1]) or np.isnan(a2[0]) or np.isnan(a2[1]):
            return np.nan
    except TypeError:
        return np.nan
    try:
        return round(geodesic(a1, a2).km, 3)
    except Exception:
        return np.nan


def transform_data(df: pd.DataFrame, stations_csv_path: str) -> pd.DataFrame:
    stations = pd.read_csv(stations_csv_path)
    for col in ['Stacja wynajmu', 'Stacja zwrotu']:
        if col in df.columns:
            s = df[col].astype(str).str.replace('\xa0', '', regex=False).str.rstrip()
            # Treat 'nan' strings back to NaN
            s = s.mask(s.eq('nan'))
            df[col] = s

    # Drop rows where either station name starts with '#'
    mask_bad = df['Stacja wynajmu'].astype(str).str.startswith('#', na=False) | \
               df['Stacja zwrotu'].astype(str).str.startswith('#', na=False)
    df = df.loc[~mask_bad].copy()

    # Merge lat/lon for start and end stations
    df = df.merge(stations, left_on='Stacja wynajmu', right_on='station_name', how='left')
    df = df.merge(stations, left_on='Stacja zwrotu', right_on='station_name', how='left', suffixes=('_start', '_end'))

    # Cleanup and rename
    drop_cols = [c for c in ['station_name_start', 'station_name_end'] if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    rename_map = {
        'UID wynajmu': 'uid',
        'Numer roweru': 'bike_number',
        'Data wynajmu': 'start_time',
        'Data zwrotu': 'end_time',
        'Stacja wynajmu': 'start_station',
        'Stacja zwrotu': 'end_station',
        'Czas trwania': 'duration',
        'lat_start': 'lat_start',
        'lon_start': 'lon_start',
        'lat_end': 'lat_end',
        'lon_end': 'lon_end',
    }
    df = df.rename(columns=rename_map)

    # Types
    if 'start_time' in df.columns:
        df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    if 'end_time' in df.columns:
        df['end_time'] = pd.to_datetime(df['end_time'], errors='coerce')
    if 'uid' in df.columns:
        df['uid'] = pd.to_numeric(df['uid'], errors='coerce').astype('Int64')
    if 'duration' in df.columns:
        df['duration'] = pd.to_numeric(df['duration'], errors='coerce').astype('Int64')

    # Distance
    for c in ['lat_start', 'lon_start', 'lat_end', 'lon_end']:
        if c not in df.columns:
            df[c] = np.nan
    df['distance'] = df.apply(distance_km, axis=1)

    # Final column order
    cols = [
        'uid', 'bike_number', 'start_time', 'end_time',
        'start_station', 'end_station', 'duration',
        'lat_start', 'lon_start', 'lat_end', 'lon_end', 'distance'
    ]
    present = [c for c in cols if c in df.columns]
    return df[present]


def create_database(db_path: str):
    ensure_dir(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bike_rides (
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
        )
        """
    )
    # Idempotency via unique uid
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS bike_rides_uid_idx ON bike_rides(uid)")
    conn.commit()
    conn.close()


def load_to_sqlite(df: pd.DataFrame, db_path: str):
    create_database(db_path)
    conn = sqlite3.connect(db_path)
    try:
        # Stage the data
        df.to_sql('staging_bike_rides', conn, if_exists='replace', index=False)
        present = list(df.columns)
        placeholders = ','.join(present)
        sql = f"INSERT OR IGNORE INTO bike_rides ({placeholders}) SELECT {placeholders} FROM staging_bike_rides"
        conn.execute(sql)
        conn.commit()
    finally:
        try:
            conn.execute('DROP TABLE IF EXISTS staging_bike_rides')
            conn.commit()
        except Exception:
            pass
        conn.close()


def main():
    root = repo_root()
    # Per docs/SPECS.md: SQLite db location: data/processed/bike_data.db
    db_path = os.path.join(root, 'data', 'processed', 'bike_data.db')
    # Use consolidated, up-to-date station coordinates
    stations_csv = os.path.join(root, 'data', 'bike_stations_coords.csv')

    # Per docs/SPECS.md directory contract
    raw_base = os.path.join(root, 'data', 'raw')
    interim_base = os.path.join(root, 'data', 'interim')

    session = make_session()
    print('Discovering latest CSV...')
    csv_urls = get_all_csv_urls(URL, session)
    latest_url, latest_filename = pick_latest_csv(csv_urls)
    if not latest_url:
        raise RuntimeError('Could not find any CSV download links on the page')
    year = 2025

    raw_dir = os.path.join(raw_base, str(year))
    interim_dir = interim_base
    ensure_dir(raw_dir)
    ensure_dir(interim_dir)

    print(f'Downloading raw file: {latest_filename}')
    raw_path = download_file(latest_url, raw_dir, session)

    print('Reading raw CSV...')
    df = pd.read_csv(raw_path, encoding='utf-8')

    print('Transforming...')
    cleaned = transform_data(df, stations_csv)

    # Save cleaned CSV (optional, helpful for debugging and ad-hoc use)
    cleaned_name = os.path.splitext(latest_filename)[0] + '_clean.csv'
    # Save cleaned CSV to data/interim per contract
    cleaned_path = os.path.join(interim_dir, cleaned_name)
    cleaned.to_csv(cleaned_path, index=False)
    print(f'Wrote cleaned CSV: {cleaned_path}')

    print('Loading into SQLite...')
    load_to_sqlite(cleaned, db_path)
    print(f'Loaded {len(cleaned)} rows (duplicates skipped by uid). DB: {db_path}')


if __name__ == '__main__':
    main()
