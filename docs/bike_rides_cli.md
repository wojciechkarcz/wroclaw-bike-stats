# Bike Rides CLI

The `bike_rides_cli.py` script consolidates downloading, transforming and loading daily bike ride CSV files.

## Usage

Run the script with one of the subcommands:

```bash
python src/bike_rides_cli.py <command> [options]
```

### Commands

- `latest` – download the most recent CSV file.
- `date <YYYY-MM-DD>` – download data for a specific day.
- `all` – fetch every available CSV file.
- `load-folder <path>` – process CSV files that are already downloaded in `path`.

### Options

Data is transformed and loaded into SQLite by default. Use the following flags to skip steps:

- `--no-transform` – keep only raw CSV downloads.
- `--no-sqlite` – skip loading cleaned data into `data/processed/bike_data.db`.

Cleaned CSV files are always written to `data/interim` and raw files to `data/raw/<year>`.

## Examples

Download the latest file and load it into the database:

```bash
python src/bike_rides_cli.py latest
```

Download rides for 2025-08-20 without transforming:

```bash
python src/bike_rides_cli.py date 2025-08-20 --no-transform
```

Process existing files from a folder and load them into SQLite:

```bash
python src/bike_rides_cli.py load-folder data/raw/2025
```
