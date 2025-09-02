/*
  Static web app for Wrocław Bike Stats
  - Loads data from /data/processed/metrics/bikes-2025.json
  - Single day view: summary, histogram, top stations/routes
  - Date range view: line charts, averaged histogram, aggregated lists
*/

const DATA_URL = '/data/rides.json';

const state = {
  raw: null, // full JSON
  dates: [], // sorted list of available dates (strings YYYY-MM-DD)
};

function byId(id){ return document.getElementById(id); }

async function loadData(){
  const res = await fetch(DATA_URL, { cache: 'no-cache' });
  if(!res.ok) throw new Error('Failed to load data: '+res.status);
  const json = await res.json();
  state.raw = json;
  state.dates = Object.keys(json.days || {}).sort();
}

function setActiveView(id){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  byId(id).classList.add('active');
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active', b.dataset.target === id));
  // Re-render range charts after becoming visible so Chart.js can size correctly
  if (id === 'range-view'){
    const start = byId('range-start')?.value;
    const end = byId('range-end')?.value;
    if (start && end) updateRange(start, end);
  }
}

function format(num){
  if (num == null) return '-';
  return Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(num);
}

function renderCards(container, entries){
  container.innerHTML = '';
  entries.forEach(([k,v])=>{
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `<div class="k">${k}</div><div class="v">${format(v)}</div>`;
    container.appendChild(el);
  });
}

function renderList(container, items, formatter){
  container.innerHTML = '';
  items.forEach((item)=>{
    const li = document.createElement('li');
    li.textContent = formatter(item);
    container.appendChild(li);
  });
}

function toDate(s){ return new Date(s+'T00:00:00'); }
function clampDate(s, min, max){
  if (s < min) return min; if (s > max) return max; return s;
}

// Date helpers bound to available dates list
function isAvailableDate(ds){ return state.dates.includes(ds); }
function lowerBound(arr, target){
  let lo = 0, hi = arr.length;
  while (lo < hi){
    const mid = (lo + hi) >> 1;
    if (arr[mid] < target) lo = mid + 1; else hi = mid;
  }
  return lo; // first index with arr[i] >= target
}
function nearestAvailableAny(target){
  if (!state.dates.length) return target;
  const i = lowerBound(state.dates, target);
  if (i < state.dates.length && state.dates[i] === target) return target;
  const prev = i-1 >= 0 ? state.dates[i-1] : null;
  const next = i < state.dates.length ? state.dates[i] : null;
  if (prev && next){
    // pick the closer one; tie -> earlier (prev)
    const td = (a,b)=> Math.abs((new Date(a)) - (new Date(b)));
    return td(prev, target) <= td(next, target) ? prev : next;
  }
  return prev || next || target;
}
function nearestOnOrBefore(target){
  if (!state.dates.length) return target;
  const i = lowerBound(state.dates, target);
  if (i < state.dates.length && state.dates[i] === target) return target;
  return (i-1>=0) ? state.dates[i-1] : state.dates[0];
}
function nearestOnOrAfter(target){
  if (!state.dates.length) return target;
  const i = lowerBound(state.dates, target);
  return (i < state.dates.length) ? state.dates[i] : state.dates[state.dates.length-1];
}

// SINGLE DAY VIEW
function updateSingle(dateStr){
  const d = state.raw.days[dateStr];
  if(!d){
    byId('single-summary').innerHTML = '<div class="card">No data for selected date.</div>';
    byId('single-histogram').innerHTML = '';
    byId('single-busiest').innerHTML = '';
    byId('single-routes').innerHTML = '';
    return;
  }
  renderCards(byId('single-summary'), [
    ['Total rides', d.total_rides],
    ['Avg distance (km)', d.avg_distance_km],
    ['Avg duration (min)', d.avg_duration_min],
    ['Total distance (km)', d.total_distance_km],
    ['Total duration (min)', d.total_duration_min],
    ['Round trips', d.round_trips],
    ['Left outside station', d.left_outside_station],
  ]);

  // Histogram bars 0..23
  const hist = Array.from({length:24}, (_,h)=>({ x: String(h), y: d.bike_rentals_histogram[String(h)] || 0 }));
  SimpleCharts.barChart(byId('single-histogram'), hist, { xLabel: 'Hour', yLabel: 'Number of rentals' });

  renderStationsTable(byId('single-busiest'), (d.busiest_stations_top5||[]));
  renderRoutesTable(byId('single-routes'), (d.top_routes_top5||[]));
}

// DATE RANGE VIEW
const METRICS = [
  { key:'total_rides', label:'Total rides' },
  { key:'avg_distance_km', label:'Avg distance (km)' },
  { key:'avg_duration_min', label:'Avg duration (min)' },
  { key:'total_distance_km', label:'Total distance (km)' },
  { key:'total_duration_min', label:'Total duration (min)' },
  { key:'round_trips', label:'Round trips' },
  { key:'left_outside_station', label:'Left outside station' },
];

function filterDatesInRange(start, end){
  return state.dates.filter(d => d >= start && d <= end);
}

function aggregateHistogramAvg(dates){
  const sums = Array(24).fill(0);
  dates.forEach(ds => {
    const h = state.raw.days[ds].bike_rentals_histogram || {};
    for(let hour=0; hour<24; hour++) sums[hour] += (h[String(hour)]||0);
  });
  const n = Math.max(1, dates.length);
  return sums.map((v,i)=>({ x:String(i), y: Math.round(v/n) }));
}

function aggregateBusiestStations(dates, topN=5){
  const map = new Map();
  dates.forEach(ds => {
    (state.raw.days[ds].busiest_stations_top5||[]).forEach(s=>{
      const cur = map.get(s.station) || { arrivals:0, departures:0, total:0 };
      map.set(s.station, {
        arrivals: cur.arrivals + (s.arrivals||0),
        departures: cur.departures + (s.departures||0),
        total: cur.total + (s.total||0)
      });
    });
  });
  return [...map.entries()]
    .map(([station,vals])=>({station, ...vals}))
    .sort((a,b)=>b.total-a.total)
    .slice(0,topN);
}

function aggregateTopRoutes(dates, topN=5){
  const map = new Map();
  const keyOf = (r)=> `${r.start_station} → ${r.end_station}`;
  dates.forEach(ds => {
    (state.raw.days[ds].top_routes_top5||[]).forEach(r=>{
      const k = keyOf(r);
      const cur = map.get(k) || 0;
      map.set(k, cur + (r.rides||0));
    });
  });
  return [...map.entries()].sort((a,b)=>b[1]-a[1]).slice(0,topN).map(([route,rides])=>({route,rides}));
}

function updateRange(start, end){
  if (!start || !end) return;
  const dates = filterDatesInRange(start, end);
  const host = byId('range-metrics');
  host.innerHTML = '';
  METRICS.forEach(m => {
    const card = document.createElement('div');
    card.className = 'card';
    const title = document.createElement('div');
    title.className = 'k';
    title.textContent = m.label;
    const chartEl = document.createElement('div');
    chartEl.className = 'chart';
    card.appendChild(title); card.appendChild(chartEl);
    host.appendChild(card);
    const series = dates.map((ds)=>({ x: ds, y: state.raw.days[ds][m.key] || 0 }));
    SimpleCharts.lineChart(chartEl, series, { yLabel: m.label, xLabel: 'Date' });
  });

  SimpleCharts.barChart(byId('range-histogram'), aggregateHistogramAvg(dates), { xLabel: 'Hour', yLabel: 'Number of rentals' });

  const stations = aggregateBusiestStations(dates);
  renderStationsTable(byId('range-busiest'), stations);

  const routes = aggregateTopRoutes(dates);
  renderRoutesTable(byId('range-routes'), routes);
}

function initTabs(){
  document.querySelectorAll('.view-switch .tab').forEach(btn=>{
    btn.addEventListener('click', ()=> setActiveView(btn.dataset.target));
  });
}

function initDates(){
  const min = state.dates[0];
  const max = state.dates[state.dates.length-1];
  const single = byId('single-date');
  single.min = min; single.max = max; single.value = max;
  single.addEventListener('change', ()=>{
    let v = clampDate(single.value, min, max);
    if (!isAvailableDate(v)) v = nearestAvailableAny(v);
    single.value = v;
    updateSingle(v);
  });
  updateSingle(single.value);
  byId('single-date-label').textContent = formatLongDate(single.value);
  single.addEventListener('change', ()=>{
    byId('single-date-label').textContent = formatLongDate(single.value);
  });

  const start = byId('range-start');
  const end = byId('range-end');
  start.min = min; start.max = max; end.min = min; end.max = max;
  // default to last 7 days if possible
  const endVal = max;
  const startIdx = Math.max(0, state.dates.length-7);
  const startVal = state.dates[startIdx];
  start.value = startVal; end.value = endVal;
  const onChange = ()=>{
    let s = clampDate(start.value, min, max);
    let e = clampDate(end.value, min, max);
    // snap to available dates with intuitive semantics for range
    if (!isAvailableDate(s)) s = nearestOnOrBefore(s);
    if (!isAvailableDate(e)) e = nearestOnOrAfter(e);
    // enforce ordering: end >= start
    if (e < s) e = nearestOnOrAfter(s);
    // reflect back to inputs and tighten bounds
    start.value = s; end.value = e;
    start.max = e; end.min = s;
    if (s && e && s <= e) updateRange(s, e);
    byId('range-date-label').textContent = `${formatLongDate(s)} - ${formatLongDate(e)}`;
  };
  start.addEventListener('change', onChange);
  end.addEventListener('change', onChange);
  onChange();
}

async function main(){
  initTabs();
  try {
    await loadData();
    initDates();
  } catch (e){
    console.error(e);
    document.querySelector('.container').innerHTML = `<div class="panel">${String(e)}</div>`;
  }
}

document.addEventListener('DOMContentLoaded', main);

// Helpers for tables and date labels
function el(tag, props={}, children=[]) {
  const e = document.createElement(tag);
  Object.assign(e, props);
  children.forEach(c => e.appendChild(c));
  return e;
}

function renderStationsTable(container, rows){
  container.innerHTML = '';
  const table = el('table', { className: 'table' });
  const thead = el('thead', {}, [
    el('tr', {}, [
      el('th', { textContent: 'Station' }),
      el('th', { textContent: 'Arrivals' }),
      el('th', { textContent: 'Departures' }),
      el('th', { textContent: 'Total' })
    ])
  ]);
  const tbody = el('tbody');
  (rows||[]).forEach(r => {
    const tr = el('tr', {}, [
      el('td', { textContent: r.station }),
      el('td', { textContent: r.arrivals ?? '-' }),
      el('td', { textContent: r.departures ?? '-' }),
      el('td', { textContent: r.total ?? '-' })
    ]);
    tbody.appendChild(tr);
  });
  table.appendChild(thead); table.appendChild(tbody);
  container.appendChild(table);
}

function renderRoutesTable(container, rows){
  container.innerHTML = '';
  const table = el('table', { className: 'table' });
  const thead = el('thead', {}, [
    el('tr', {}, [
      el('th', { textContent: 'Start' }),
      el('th', { textContent: 'End' }),
      el('th', { textContent: 'Rides' })
    ])
  ]);
  const tbody = el('tbody');
  (rows||[]).forEach(r => {
    // rows for single day have start_station/end_station; aggregated have route string
    if (r.start_station){
      const tr = el('tr', {}, [
        el('td', { textContent: r.start_station }),
        el('td', { textContent: r.end_station }),
        el('td', { textContent: r.rides ?? '-' })
      ]);
      tbody.appendChild(tr);
    } else {
      const parts = String(r.route||'').split(' → ');
      const tr = el('tr', {}, [
        el('td', { textContent: parts[0] || '' }),
        el('td', { textContent: parts[1] || '' }),
        el('td', { textContent: r.rides ?? '-' })
      ]);
      tbody.appendChild(tr);
    }
  });
  table.appendChild(thead); table.appendChild(tbody);
  container.appendChild(table);
}

function formatLongDate(yyyy_mm_dd){
  if (!yyyy_mm_dd) return '';
  const d = new Date(yyyy_mm_dd + 'T00:00:00');
  return d.toLocaleDateString(undefined, { day:'numeric', month:'long', year:'numeric' });
}
