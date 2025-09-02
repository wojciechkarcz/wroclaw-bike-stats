/*
  Static web app for Wrocław Bike Stats
  - Loads data from /data/processed/metrics/bikes-2025.json
  - Single day view: summary, histogram, top stations/routes
  - Date range view: line charts, averaged histogram, aggregated lists
*/

const DATA_URL = '/data/processed/metrics/bikes-2025.json';

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
  SimpleCharts.barChart(byId('single-histogram'), hist);

  renderList(byId('single-busiest'), (d.busiest_stations_top5||[]), s=>`${s.station} — ${s.total}`);
  renderList(byId('single-routes'), (d.top_routes_top5||[]), r=>`${r.start_station} → ${r.end_station} — ${r.rides}`);
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
      const cur = map.get(s.station) || 0;
      map.set(s.station, cur + (s.total||0));
    });
  });
  return [...map.entries()].sort((a,b)=>b[1]-a[1]).slice(0,topN).map(([station,total])=>({station,total}));
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
    SimpleCharts.lineChart(chartEl, series);
  });

  SimpleCharts.barChart(byId('range-histogram'), aggregateHistogramAvg(dates));

  const stations = aggregateBusiestStations(dates);
  renderList(byId('range-busiest'), stations, s=>`${s.station} — ${s.total}`);

  const routes = aggregateTopRoutes(dates);
  renderList(byId('range-routes'), routes, r=>`${r.route} — ${r.rides}`);
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
  single.addEventListener('change', ()=> updateSingle(clampDate(single.value, min, max)));
  updateSingle(single.value);

  const start = byId('range-start');
  const end = byId('range-end');
  start.min = min; start.max = max; end.min = min; end.max = max;
  // default to last 7 days if possible
  const endVal = max;
  const startIdx = Math.max(0, state.dates.length-7);
  const startVal = state.dates[startIdx];
  start.value = startVal; end.value = endVal;
  const onChange = ()=>{
    const s = clampDate(start.value, min, max);
    const e = clampDate(end.value, min, max);
    if (s && e && s <= e) updateRange(s, e);
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

