# TASKS

## Project Status
- M0 Setup (in progress)
- M1 Data Ingest (in progress)
- M2 Metrics
- M3 UI
- M4 Polish
- M5 Next features

## Active Task
[T-02] M1 – Finish raw data loading script 
- Goal: the `src/data_load_sqlite.py` script is almost done, check if everything is right, especially paths following rules in `docs/SPECS.md`
- Acceptance:
  - downloads the most recent csv file 
  - transforms the data and stores in SQLite db
  - saves cleaned data into separate csv file
- create at least 1 test for that script
- Note: don't change the script much, just check if it is OK

## Ready (next up)
[T-03] M0 – Create a Makefile
- Goal: I want to have some very basic Makefile with commands I can use to test parts of my project

[T-04] M2 – Compute first metric
- calculate the first metric from point 4 in `docs/SPECS.md`

[T-05] M2 – Create tests for all metrics
- create tests for all metrics listed in SPECS

## Done (recent)
[T-01] M1 - Basic project setup - 2025-08-18