# 2025-09-08

## #15 - Script for calculating general metrics

- Summary: Implement daily metrics CLI that computes per-day metrics and writes yearly JSON aggregates; add tests; introduce minimal HTML viewer; apply filters/exclusions and performance improvements; update bike station coordinates data.
- Decisions/Assumptions: Durations measured in minutes; histogram buckets by start hour; script reads from any SQLite table (uses `sample_data` for tests); yearly mode appends/merges by date to avoid full rewrites; outputs under `data/processed/metrics/<year>.json`.

