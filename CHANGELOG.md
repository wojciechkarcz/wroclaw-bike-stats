## #16 - Web app for displaying bike rides data (2025-09-08)

- Scaffold static web UI under `/web` with Single Day and Date Range views.
- Line charts via Chart.js (tooltips, rotated x ticks, Y from 0); SVG fallback kept.
- Date validation and snapping to available dates; ensure `end >= start` with bound updates.
- Single Day: histogram with axes and value-on-hover; busiest stations and top routes as tables; default to latest date.
- Date Range: stacked daily metric charts; averaged hourly histogram; busiest stations and top routes as tables; default last 7 days.
- New: adaptive x-axis tick density for Date Range charts based on container width.
- Data served from `/web/data/rides.json` copied from processed metrics.

Key decisions/assumptions:
- Use Chart.js for richer interactivity; keep minimal SVG fallback.
- Serve `web/` as site root so `/data/rides.json` is reachable.
