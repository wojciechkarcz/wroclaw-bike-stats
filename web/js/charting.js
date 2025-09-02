// Minimal SVG chart helpers: line chart and bar chart with hover tooltips.

function createSvg(width, height) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.style.background = '#fff';
  return svg;
}

function drawAxes(svg, m, w, h, xTicks, yTicks, labels){
  const ns = svg.namespaceURI;
  const axis = document.createElementNS(ns, 'g');
  axis.setAttribute('stroke', '#9ca3af');
  axis.setAttribute('stroke-width', '1');
  axis.setAttribute('fill', 'none');
  // X axis line
  const xLine = document.createElementNS(ns, 'line');
  xLine.setAttribute('x1', m.l); xLine.setAttribute('x2', m.l + w);
  xLine.setAttribute('y1', m.t + h); xLine.setAttribute('y2', m.t + h);
  axis.appendChild(xLine);
  // Y axis line
  const yLine = document.createElementNS(ns, 'line');
  yLine.setAttribute('x1', m.l); yLine.setAttribute('x2', m.l);
  yLine.setAttribute('y1', m.t); yLine.setAttribute('y2', m.t + h);
  axis.appendChild(yLine);

  const labelGroup = document.createElementNS(ns, 'g');
  labelGroup.setAttribute('fill', '#6b7280');
  labelGroup.setAttribute('font-size', '10');

  // X ticks
  xTicks.forEach(t => {
    const g = document.createElementNS(ns, 'g');
    const x = t.x;
    const line = document.createElementNS(ns,'line');
    line.setAttribute('x1', x); line.setAttribute('x2', x);
    line.setAttribute('y1', m.t + h); line.setAttribute('y2', m.t + h + 4);
    line.setAttribute('stroke', '#9ca3af');
    g.appendChild(line);
    if (t.label != null){
      const text = document.createElementNS(ns,'text');
      text.setAttribute('x', x);
      text.setAttribute('y', m.t + h + 14);
      text.setAttribute('text-anchor', 'middle');
      text.textContent = t.label;
      g.appendChild(text);
    }
    labelGroup.appendChild(g);
  });

  // Y ticks
  yTicks.forEach(t => {
    const g = document.createElementNS(ns, 'g');
    const y = t.y;
    const line = document.createElementNS(ns,'line');
    line.setAttribute('x1', m.l - 4); line.setAttribute('x2', m.l);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    line.setAttribute('stroke', '#9ca3af');
    g.appendChild(line);
    if (t.label != null){
      const text = document.createElementNS(ns,'text');
      text.setAttribute('x', m.l - 6);
      text.setAttribute('y', y + 3);
      text.setAttribute('text-anchor', 'end');
      text.textContent = t.label;
      g.appendChild(text);
    }
    labelGroup.appendChild(g);
  });

  // Axis labels
  if (labels && labels.x){
    const text = document.createElementNS(ns,'text');
    text.setAttribute('x', m.l + w/2);
    text.setAttribute('y', m.t + h + 28);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#374151');
    text.setAttribute('font-size', '11');
    text.textContent = labels.x;
    labelGroup.appendChild(text);
  }
  if (labels && labels.y){
    const text = document.createElementNS(ns,'text');
    text.setAttribute('transform', `translate(${m.l - 36} ${m.t + h/2}) rotate(-90)`);
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('fill', '#374151');
    text.setAttribute('font-size', '11');
    text.textContent = labels.y;
    labelGroup.appendChild(text);
  }

  svg.appendChild(axis);
  svg.appendChild(labelGroup);
}

function lineChart(container, series, opts={}){
  const width = opts.width || 720; const height = opts.height || 240;
  const m = {l:44,r:10,t:10,b:34};
  const w = width - m.l - m.r; const h = height - m.t - m.b;
  const svg = createSvg(width,height);
  container.innerHTML=''; container.appendChild(svg);

  if (!series || series.length === 0) return;
  const xs = series.map(p=>p.x);
  const ys = series.map(p=>p.y);
  const xMin = 0, xMax = series.length-1;
  // Force Y axis to start at 0
  const yMin = 0;
  const yMax = Math.max(1, ...ys);
  const niceMax = yMax === yMin ? yMax+1 : yMax;

  const toX = (i)=> m.l + (i - xMin) * (w/(xMax - xMin || 1));
  const toY = (v)=> m.t + h - (v - yMin) * (h/(niceMax - yMin || 1));

  // grid
  const grid = document.createElementNS(svg.namespaceURI,'g');
  grid.setAttribute('stroke','#e5e7eb'); grid.setAttribute('stroke-width','1'); grid.setAttribute('fill','none');
  for (let i=0;i<5;i++){
    const y = m.t + (h*i/4);
    const line = document.createElementNS(svg.namespaceURI,'line');
    line.setAttribute('x1', m.l); line.setAttribute('x2', m.l+w);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    grid.appendChild(line);
  }
  svg.appendChild(grid);

  // axes
  const xTickIdx = (len)=>{
    if (len <= 2) return [0, len-1];
    if (len <= 5) return [0, Math.floor(len/2), len-1];
    return [0, Math.floor(len/2), len-1];
  };
  const xTicks = xTickIdx(series.length).map(i=>({ x: toX(i), label: String(series[i].x) }));
  const yTicks = [0,0.25,0.5,0.75,1].map(frac=>{
    const v = yMin + frac*(niceMax - yMin || 1);
    return { y: toY(v), label: Math.round(v) };
  });
  drawAxes(svg, m, w, h, xTicks, yTicks, { x: opts.xLabel || '', y: opts.yLabel || '' });

  // If Chart.js is available, prefer it for richer UX
  if (window.Chart){
    container.innerHTML = '';
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    container.appendChild(canvas);
    if (container._chart) { try { container._chart.destroy(); } catch(e){} }
    const labels = series.map(p=>p.x);
    const data = series.map(p=>p.y);
    // Ensure canvas has actual pixel size even if parent was hidden before
    const rect = container.getBoundingClientRect();
    const cw = Math.max(1, Math.floor(rect.width)) || (opts.width || 720);
    const ch = Math.max(1, Math.floor(rect.height)) || (opts.height || 240);
    canvas.width = cw; canvas.height = ch;
    const chart = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: opts.yLabel || 'Value',
          data,
          borderColor: opts.color || '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.15)',
          borderWidth: 2,
          fill: false,
          pointRadius: 3,
          pointHoverRadius: 4,
          tension: 0.2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        spanGaps: true,
        scales: {
          x: {
            type: 'category',
            ticks: {
              autoSkip: false,
              maxRotation: 45,
              minRotation: 45,
            },
            title: { display: !!opts.xLabel, text: opts.xLabel || '' }
          },
          y: {
            beginAtZero: true,
            title: { display: !!opts.yLabel, text: opts.yLabel || '' }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true }
        }
      }
    });
    container._chart = chart;
    return; // done
  }

  // path (fallback SVG implementation)
  const d = series.map((p,i)=> `${i===0?'M':'L'} ${toX(i)} ${toY(p.y)}`).join(' ');
  const path = document.createElementNS(svg.namespaceURI,'path');
  path.setAttribute('d', d);
  path.setAttribute('fill','none');
  path.setAttribute('stroke', opts.color || '#2563eb');
  path.setAttribute('stroke-width','2');
  svg.appendChild(path);

  // points
  const pts = document.createElementNS(svg.namespaceURI,'g');
  const points = [];
  for (let i=0;i<series.length;i++){
    const c = document.createElementNS(svg.namespaceURI,'circle');
    const cx = toX(i); const cy = toY(series[i].y);
    c.setAttribute('cx', cx);
    c.setAttribute('cy', cy);
    c.setAttribute('r', 3);
    c.setAttribute('fill', '#2563eb');
    pts.appendChild(c);
    points.push({x: cx, y: cy});
  }
  svg.appendChild(pts);

  // hover (nearest point)
  const tip = document.createElement('div');
  tip.className = 'tooltip';
  tip.style.display = 'none';
  container.style.position = 'relative';
  container.appendChild(tip);

  svg.addEventListener('mousemove', (e)=>{
    const rect = svg.getBoundingClientRect();
    const scaleX = rect.width / width;
    const scaleY = rect.height / height;
    const px = e.clientX - rect.left;
    // invert to nearest index using pixel coords and scale
    const inv = (px - m.l*scaleX) / ((w*scaleX)/(xMax - xMin || 1));
    const i = Math.max(0, Math.min(series.length-1, Math.round(inv)));
    const sx = toX(i) * scaleX;
    const sy = toY(series[i].y) * scaleY;
    // Only show when close to the point
    const dx = px - sx;
    const py = e.clientY - rect.top;
    const dy = py - sy;
    const dist = Math.sqrt(dx*dx + dy*dy);
    if (dist <= (opts.hoverRadius || 12)){
      tip.style.left = `${sx}px`;
      tip.style.top = `${sy}px`;
      tip.innerText = `${series[i].x}: ${series[i].y}`;
      tip.style.display = 'block';
    } else {
      tip.style.display = 'none';
    }
  });
  svg.addEventListener('mouseleave', ()=>{ tip.style.display='none'; });
}

function barChart(container, values, opts={}){
  const width = opts.width || 720; const height = opts.height || 240;
  const m = {l:44,r:10,t:10,b:34};
  const w = width - m.l - m.r; const h = height - m.t - m.b;
  const svg = createSvg(width,height);
  container.innerHTML=''; container.appendChild(svg);

  const maxV = Math.max(1, ...values.map(v=>v.y));
  const bw = w / values.length;
  const toY = (v)=> m.t + h - (v/maxV)*h;

  // grid
  const grid = document.createElementNS(svg.namespaceURI,'g');
  grid.setAttribute('stroke','#e5e7eb'); grid.setAttribute('stroke-width','1'); grid.setAttribute('fill','none');
  for (let i=0;i<5;i++){
    const y = m.t + (h*i/4);
    const line = document.createElementNS(svg.namespaceURI,'line');
    line.setAttribute('x1', m.l); line.setAttribute('x2', m.l+w);
    line.setAttribute('y1', y); line.setAttribute('y2', y);
    grid.appendChild(line);
  }
  svg.appendChild(grid);

  // axes with ticks
  const xTicks = [];
  const hoursToShow = [0,6,12,18,23];
  hoursToShow.forEach(hr => {
    const x = m.l + hr * bw + bw/2;
    xTicks.push({ x, label: String(hr) });
  });
  const yTicks = [0,0.25,0.5,0.75,1].map(frac=>{
    const v = frac*maxV;
    return { y: toY(v), label: Math.round(v) };
  });
  drawAxes(svg, m, w, h, xTicks, yTicks, { x: opts.xLabel || '', y: opts.yLabel || '' });

  const bars = document.createElementNS(svg.namespaceURI,'g');
  bars.setAttribute('fill', opts.color || '#2563eb');
  values.forEach((v,i)=>{
    const x = m.l + i*bw + 2;
    const y = toY(v.y);
    const rect = document.createElementNS(svg.namespaceURI,'rect');
    rect.setAttribute('x', x);
    rect.setAttribute('y', y);
    rect.setAttribute('width', Math.max(1,bw-4));
    rect.setAttribute('height', Math.max(0, m.t+h - y));
    rect.setAttribute('rx', 2);
    rect.dataset.label = v.x;
    rect.dataset.value = v.y;
    bars.appendChild(rect);
  });
  svg.appendChild(bars);

  // hover tooltip
  const tip = document.createElement('div');
  tip.className = 'tooltip';
  tip.style.display = 'none';
  container.style.position = 'relative';
  container.appendChild(tip);
  svg.addEventListener('mousemove', (e)=>{
    const target = e.target;
    if (target && target.tagName === 'rect'){
      const bbox = target.getBoundingClientRect();
      tip.style.left = `${bbox.left + bbox.width/2 - svg.getBoundingClientRect().left}px`;
      tip.style.top = `${bbox.top - svg.getBoundingClientRect().top}px`;
      // histograms: show value only
      tip.innerText = `${target.dataset.value}`;
      tip.style.display = 'block';
    }
  });
  svg.addEventListener('mouseleave', ()=>{ tip.style.display='none'; });
}

window.SimpleCharts = { lineChart, barChart };
