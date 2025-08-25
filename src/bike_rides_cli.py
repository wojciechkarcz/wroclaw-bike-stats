import argparse
import os
import datetime as dt
from urllib.parse import urlparse

import pandas as pd

from data_load_sqlite import (
    URL,
    repo_root,
    make_session,
    ensure_dir,
    get_all_csv_urls,
    pick_latest_csv,
    download_file,
    extract_dt_from_filename,
    transform_data,
    load_to_sqlite,
)


def _process_paths(paths: list[str], transform: bool, to_sqlite: bool) -> None:
    """Transform CSV files and optionally load them to SQLite."""
    root = repo_root()
    stations_csv = os.path.join(root, "data", "bike_stations.csv")
    interim_dir = os.path.join(root, "data", "interim")
    db_path = os.path.join(root, "data", "processed", "bike_data.db")

    ensure_dir(interim_dir)
    if to_sqlite:
        ensure_dir(os.path.dirname(db_path))

    for raw_path in paths:
        if transform or to_sqlite:
            df = pd.read_csv(raw_path, encoding="utf-8")
            cleaned = transform_data(df, stations_csv)
            cleaned_name = os.path.splitext(os.path.basename(raw_path))[0] + "_clean.csv"
            cleaned_path = os.path.join(interim_dir, cleaned_name)
            cleaned.to_csv(cleaned_path, index=False)
            if to_sqlite:
                load_to_sqlite(cleaned, db_path)
        # When transform is False we simply keep the raw download.


def _download_and_process(urls: list[str], transform: bool, to_sqlite: bool) -> None:
    session = make_session()
    root = repo_root()
    raw_base = os.path.join(root, "data", "raw")

    paths: list[str] = []
    for url in urls:
        filename = os.path.basename(urlparse(url).path)
        dtv = extract_dt_from_filename(filename)
        year = dtv.year if dtv else dt.datetime.now().year
        raw_dir = os.path.join(raw_base, str(year))
        ensure_dir(raw_dir)
        path = download_file(url, raw_dir, session)
        paths.append(path)

    _process_paths(paths, transform, to_sqlite)


def cmd_latest(args: argparse.Namespace) -> None:
    session = make_session()
    csv_urls = get_all_csv_urls(URL, session)
    url, _ = pick_latest_csv(csv_urls)
    if not url:
        raise SystemExit("No CSV links found")
    _download_and_process([url], args.transform, args.sqlite)


def cmd_date(args: argparse.Namespace) -> None:
    target = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    session = make_session()
    csv_urls = get_all_csv_urls(URL, session)
    matches = []
    for u in csv_urls:
        fn = os.path.basename(urlparse(u).path)
        dtv = extract_dt_from_filename(fn)
        if dtv and dtv.date() == target:
            matches.append(u)
    if not matches:
        raise SystemExit(f"No CSV found for {target}")
    _download_and_process(matches, args.transform, args.sqlite)


def cmd_all(args: argparse.Namespace) -> None:
    session = make_session()
    urls = get_all_csv_urls(URL, session)
    _download_and_process(urls, args.transform, args.sqlite)


def cmd_load(args: argparse.Namespace) -> None:
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        raise SystemExit(f"Folder not found: {folder}")
    paths = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith(".csv")
    ]
    if not paths:
        raise SystemExit(f"No CSV files in {folder}")
    _process_paths(paths, args.transform, args.sqlite)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bike rides ETL utility")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--no-transform",
        dest="transform",
        action="store_false",
        help="Skip data transformation",
    )
    common.add_argument(
        "--no-sqlite",
        dest="sqlite",
        action="store_false",
        help="Do not load data into SQLite",
    )

    latest = sub.add_parser("latest", parents=[common], help="Download latest CSV")
    latest.set_defaults(func=cmd_latest)

    date = sub.add_parser("date", parents=[common], help="Download CSV for a specific date")
    date.add_argument("date", help="Date in YYYY-MM-DD format")
    date.set_defaults(func=cmd_date)

    all_cmd = sub.add_parser("all", parents=[common], help="Download all available CSV files")
    all_cmd.set_defaults(func=cmd_all)

    load = sub.add_parser("load-folder", parents=[common], help="Process existing CSV files in a folder")
    load.add_argument("folder", help="Folder with CSV files")
    load.set_defaults(func=cmd_load)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
