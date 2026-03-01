async function fetchJSON(path, opts){
  const res = await fetch(path, opts);
  return res.json();
}

function fmt(n, digits=2){return (typeof n === 'number')? n.toFixed(digits): n}

function renderFactory(m){
  const el = document.getElementById('factory');
  el.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <div class="small">Total production</div>
        <div style="font-size:20px;font-weight:600">${m.total_production} units</div>
      </div>
      <div>
        <div class="small">Total productive time</div>
        <div>${fmt(m.total_productive_time)}</div>
      </div>
      <div>
        <div class="small">Avg production rate</div>
        <div>${fmt(m.avg_production_rate)}</div>
      </div>
      <div>
        <div class="small">Avg worker utilization</div>
        <div>${fmt(m.avg_worker_utilization,1)}%</div>
      </div>
    </div>`;
}

function renderWorkers(wm){
  const cont = document.getElementById('workers');
  let html = '<table><tr><th>Worker</th><th>Active (hrs)</th><th>Idle (hrs)</th><th>Util%</th><th>Units</th><th>Units/hr</th></tr>';
  for(const [wid, v] of Object.entries(wm)){
    html += `<tr data-wid="${wid}"><td><a href="#" class="selWorker">${v.name} (${wid})</a></td><td>${fmt(v.total_active_time)}</td><td>${fmt(v.total_idle_time)}</td><td>${fmt(v.utilization,1)}</td><td>${v.units_produced}</td><td>${fmt(v.units_per_hour)}</td></tr>`;
  }
  html += '</table>';
  cont.innerHTML = html;
  document.querySelectorAll('.selWorker').forEach(a=>a.addEventListener('click', (ev)=>{
    ev.preventDefault();
    const row = ev.target.closest('tr');
    const wid = row.getAttribute('data-wid');
    showDetails('worker', wid);
  }));
}

function renderStations(sm){
  const cont = document.getElementById('stations');
  let html = '<table><tr><th>Station</th><th>Occupancy (hrs)</th><th>Util%</th><th>Units</th><th>Throughput</th></tr>';
  for(const [sid, v] of Object.entries(sm)){
    html += `<tr data-sid="${sid}"><td><a href="#" class="selStation">${v.name} (${sid})</a></td><td>${fmt(v.occupancy_time)}</td><td>${fmt(v.utilization,1)}</td><td>${v.units_produced}</td><td>${fmt(v.throughput)}</td></tr>`;
  }
  html += '</table>';
  cont.innerHTML = html;
  document.querySelectorAll('.selStation').forEach(a=>a.addEventListener('click', (ev)=>{
    ev.preventDefault();
    const row = ev.target.closest('tr');
    const sid = row.getAttribute('data-sid');
    showDetails('station', sid);
  }));
}

function showDetails(type, id){
  const details = document.getElementById('details');
  if(type === 'worker'){
    const m = window.lastMetrics.worker_metrics[id];
    details.innerHTML = `<div><strong>${m.name} (${id})</strong></div><div class="small">Active: ${fmt(m.total_active_time)} hrs • Idle: ${fmt(m.total_idle_time)} hrs</div><div style="margin-top:8px">Units produced: <strong>${m.units_produced}</strong></div><div style="margin-top:8px"><button class="btn" id="btnSendEvent">Send 'product_count' for ${id}</button></div>`;
    document.getElementById('btnSendEvent').addEventListener('click', ()=>{
      sendEvent({worker_id:id, workstation_id:null, event_type:'product_count', count:1});
    });
  } else {
    const m = window.lastMetrics.station_metrics[id];
    details.innerHTML = `<div><strong>${m.name} (${id})</strong></div><div class="small">Occupancy: ${fmt(m.occupancy_time)} hrs</div><div style="margin-top:8px">Units produced: <strong>${m.units_produced}</strong></div>`;
  }
}

async function sendEvent(payload){
  try{
    await fetchJSON('/events', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...payload, timestamp:new Date().toISOString()})});
    await load();
  }catch(e){
    alert('Failed to send event');
  }
}

async function populateFilters(){
  const workers = await fetchJSON('/workers');
  const stations = await fetchJSON('/workstations');
  const fw = document.getElementById('filterWorker');
  const fs = document.getElementById('filterStation');
  workers.forEach(w=>{ const o=document.createElement('option'); o.value=w.worker_id; o.textContent=`${w.name} (${w.worker_id})`; fw.appendChild(o)});
  stations.forEach(s=>{ const o=document.createElement('option'); o.value=s.station_id; o.textContent=`${s.name} (${s.station_id})`; fs.appendChild(o)});
  fw.addEventListener('change', ()=>{ if(fw.value) showDetails('worker', fw.value); else document.getElementById('details').innerHTML='<div class="small">Select a worker or station to view details.</div>'});
  fs.addEventListener('change', ()=>{ if(fs.value) showDetails('station', fs.value); else document.getElementById('details').innerHTML='<div class="small">Select a worker or station to view details.</div>'});
}

async function load(){
  const m = await fetchJSON('/metrics');
  window.lastMetrics = m;
  renderFactory(m);
  renderWorkers(m.worker_metrics);
  renderStations(m.station_metrics);
}

document.addEventListener('DOMContentLoaded', async ()=>{
  await populateFilters();
  document.getElementById('btnReseed').addEventListener('click', async ()=>{ await fetchJSON('/seed', {method:'POST'}); await load(); });
  document.getElementById('btnGenerate').addEventListener('click', async ()=>{
    const workers = await fetchJSON('/workers');
    const stations = await fetchJSON('/workstations');
    const w = workers[Math.floor(Math.random()*workers.length)];
    const s = stations[Math.floor(Math.random()*stations.length)];
    const choose = Math.random() > 0.5 ? 'working' : 'product_count';
    const payload = {worker_id: w.worker_id, workstation_id: s.station_id, event_type: choose, confidence:0.95, count: choose==='product_count'? Math.floor(Math.random()*5)+1 : 0};
    await sendEvent(payload);
  });
  await load();
});
