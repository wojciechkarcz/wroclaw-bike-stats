// Minimal SVG chart helpers: line chart and bar chart with hover tooltips.

function createSvg(width, height) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', '100%');
  svg.setAttribute('height', '100%');
  svg.style.background = '#fff';
  return svg;
}

function lineChart(container, series, opts={}){
  const width = opts.width || 720; const height = opts.height || 240;
  const m = {l:36,r:10,t:10,b:24};
  const w = width - m.l - m.r; const h = height - m.t - m.b;
  const svg = createSvg(width,height);
  container.innerHTML=''; container.appendChild(svg);

  if (!series || series.length === 0) return;
  const xs = series.map(p=>p.x);
  const ys = series.map(p=>p.y);
  const xMin = 0, xMax = series.length-1;
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
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

  // path
  const d = series.map((p,i)=> `${i===0?'M':'L'} ${toX(i)} ${toY(p.y)}`).join(' ');
  const path = document.createElementNS(svg.namespaceURI,'path');
  path.setAttribute('d', d);
  path.setAttribute('fill','none');
  path.setAttribute('stroke', opts.color || '#2563eb');
  path.setAttribute('stroke-width','2');
  svg.appendChild(path);

  // points
  const pts = document.createElementNS(svg.namespaceURI,'g');
  for (let i=0;i<series.length;i++){
    const c = document.createElementNS(svg.namespaceURI,'circle');
    c.setAttribute('cx', toX(i));
    c.setAttribute('cy', toY(series[i].y));
    c.setAttribute('r', 3);
    c.setAttribute('fill', '#2563eb');
    pts.appendChild(c);
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
    const px = e.clientX - rect.left;
    // invert to nearest index
    const i = Math.max(0, Math.min(series.length-1, Math.round((px - m.l) / (w/(xMax - xMin || 1)))));
    const sx = toX(i), sy = toY(series[i].y);
    tip.style.left = `${sx}px`;
    tip.style.top = `${sy}px`;
    tip.innerText = `${series[i].x}: ${series[i].y}`;
    tip.style.display = 'block';
  });
  svg.addEventListener('mouseleave', ()=>{ tip.style.display='none'; });
}

function barChart(container, values, opts={}){
  const width = opts.width || 720; const height = opts.height || 240;
  const m = {l:36,r:10,t:10,b:24};
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
      tip.innerText = `${target.dataset.label}: ${target.dataset.value}`;
      tip.style.display = 'block';
    }
  });
  svg.addEventListener('mouseleave', ()=>{ tip.style.display='none'; });
}

window.SimpleCharts = { lineChart, barChart };

