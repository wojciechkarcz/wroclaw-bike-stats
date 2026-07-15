# Live map — Wrocław Bike arrivals & departures

A tiny side project that turns the per-minute Nextbike API snapshots into a
"real-time" map. Every minute a cron script diffs the two latest raw JSON
snapshots and writes a single `live_events.json` file; a static HTML page
polls that file and replays the events.

Since the real sampling is once per minute, the page fakes the real-time
feeling: the batch of events from each minute is spread evenly across the
next 60 seconds (with ±1.5 s of random jitter), so markers and table rows
trickle in one by one instead of appearing all at once. The second-level
part of displayed timestamps is synthetic — the underlying data only has
minute resolution, and the events themselves are exactly the same records
that go into `data/processed/bike_status.db`.

## Files

| File | What it is |
|---|---|
| `process_events.py` | Cron script. Diffs the two latest snapshots in `data/raw/api/` (reusing `src/bike_status_changes.py`) and writes `live_events.json`. |
| `index.html` | The whole frontend: Leaflet map + two-column event table. Static, no build step. |
| `live_events.json` | Generated output, refreshed every minute. Not committed. |
| `simulate.py` | Local demo: replays test snapshots as if they were arriving live. |
| `test_snapshots/` | Five real gzipped API snapshots used by the simulator. |

## Try it locally

```bash
python3 live/simulate.py --interval 20
```

Then open <http://localhost:8000>. Every 20 seconds the simulator "receives"
the next test snapshot, regenerates `live_events.json`, and the page picks it
up on its next poll (every 10 s). With `--interval 60` it behaves exactly
like production. The simulator loops over the five test snapshots forever.

No dependencies beyond the Python standard library; Leaflet and map tiles
are loaded from CDNs by the browser.

## Deploy

1. Copy `index.html` to your web root (any static hosting works).
2. Add the processor to cron, right after the snapshot downloader, and point
   `--output` at the same web root so `live_events.json` sits next to
   `index.html`:

   ```cron
   * * * * * cd /path/to/wroclaw-bike-stats && python3 live/process_events.py --output /var/www/html/live/live_events.json
   ```

   If the page is served from a different machine, write the file locally
   and add an `scp`/`rsync` step after it.

That's it — the page has no backend; it only needs `index.html` and a fresh
`live_events.json` served from the same directory.

## Output format

```json
{
  "generated_at": "2026-07-15T19:32:02+02:00",
  "previous_snapshot_at": "2026-07-15T19:31:01+02:00",
  "interval_seconds": 60,
  "event_count": 20,
  "events": [
    {
      "timestamp": "2026-07-15T19:32:02+02:00",
      "bike_id": "592022",
      "event_type": "departed",
      "station_name": "Plac Dominikański (Galeria Dominikańska)",
      "station_id": "12497516",
      "lat": 51.108004,
      "lon": 17.039528,
      "bike_type": "standard",
      "battery": null
    }
  ]
}
```

## Tuning

All the knobs live at the top of the `<script>` block in `index.html`:

| Constant | Default | Meaning |
|---|---|---|
| `POLL_MS` | 10 000 | How often the page checks for a fresh `live_events.json`. |
| `SPREAD_MS` | 60 000 | Window over which one minute's events are replayed. |
| `JITTER_MS` | 1 500 | Random ± offset around the even spread. |
| `MARKER_TTL_MS` | 60 000 | How long a marker stays on the map. |
| `ROW_TTL_MS` | 60 000 | How long a row stays in the table. |
