## Changelog

#13 - Add bike rides CLI - 2025-08-25
- Feat: consolidate CSV download and loading commands into `bike_rides_cli.py`.
- Chore: remove older standalone downloader scripts.
- Docs: add usage guide for `bike_rides_cli.py`.

#12 - Add unified pipeline and logging - 2025-08-25
- Feat: add `src/pipeline.py` orchestrating fetch and status change processing.
- Feat: central logging with rotating file handler and start/end markers.
- Chore: replace separate cron jobs with single pipeline invocation.

#11 - Wrong station name for freestanding electric bikes - 2025-08-24
- Fix: Normalize `station_name`/`station_id` to `freestanding` for any `placeType` starting with `FREESTANDING`.
- Parse: Support both `bikes` objects and `bikeNumbers` lists within places.
- Tests: Added focused tests using `data/sample/snapA.json` and `data/sample/snapB.json` plus a minimal freestanding-electric case.
- Decision: Broad match on `placeType` to handle variations; prefer generic naming for freestanding entries.
Basic project setup - 2025-08-18
Finish raw data loading script - 2025-08-19
- Goal: the `src/data_load_sqlite.py` script is almost done, check if everything is right, especially paths following rules in `docs/SPECS.md`
- Acceptance:
  - downloads the most recent csv file
  - transforms the data and stores in SQLite db
  - saves cleaned data into separate csv file
- create at least 1 test for that script
- Note: don't change the script much, just check if it is OK
Load all data to SQLite db - 2025-08-19
- Create a script called `load_to_sqlite.py` which loads all csv files from `data/raw/2025` into SQLite db
- The script should follow exactly the same process as `src/data_load_sqlite.py`
