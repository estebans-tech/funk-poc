import { apiFetch } from './api.js';
import { show, $ } from './ui.js';

// Health + auth pills
async function bootstrap(){
  try {
    const h = await fetch('/health').then(r=>r.json())
    $('health').textContent = 'health: ' + (h.status || 'unknown')
  } catch { $('health').textContent = 'health: error' }

  // kolla serverns auth-krav (utan att skicka nyckel)
  let serverAuth = 'open'
  try {
    const r = await fetch('/policies?limit=1')
    if (r.status === 401) serverAuth = 'required'
  } catch {}

  const saved = localStorage.getItem('API_KEY') || ''
  $('apikey').value = saved
  $('auth').textContent = `auth: ${serverAuth}${saved ? ', key set' : ''}`
}
window.addEventListener('DOMContentLoaded', bootstrap);

// Save/Clear API key
$('saveKey').onclick = () => {
  const v = $('apikey').value.trim();
  if(v){ localStorage.setItem('API_KEY', v); show('ok','API key saved.'); }
  $('auth').textContent = 'auth: ' + (v ? 'key set' : 'off');
};

$('clearKey').onclick = () => {
  localStorage.removeItem('API_KEY'); $('apikey').value = '';
  $('auth').textContent = 'auth: off'; show('ok','API key cleared.');
};

// Add policy
async function add(e){
  e?.preventDefault()
  const body = {
    number: $('number').value.trim(),
    holder: $('holder').value.trim(),
    premium: parseFloat($('premium').value),
    status: $('status').value.trim()
  }

  const res = await apiFetch('/policies', {
    method:'POST',
    headers:{ 'Content-Type':'application/json' },
    body: JSON.stringify(body)
  })
  
  if(res.ok){
    location.reload();
    return
  }

  let detail=''
  try {
    const j=await res.json()
    detail=j.detail||JSON.stringify(j)
  } catch {}

  if(res.status===401) show('error','Unauthorized: missing/invalid API key.')
  else if(res.status===409) show('error','Duplicate number: that policy already exists.')
  else if(res.status===422) show('error','Validation error: '+detail)
  else show('error','Error '+res.status+': '+detail)
}
$('addForm').addEventListener('submit', add)
// Export CSV
$('exportCsv').onclick = async () => {
  const q = new URLSearchParams(location.search).get('q') || '';
  const url = '/policies.csv' + (q ? ('?q=' + encodeURIComponent(q)) : '');
  const res = await apiFetch(url);
  if(!res.ok){
    let d=''; try{ const j=await res.json(); d=j.detail||JSON.stringify(j);}catch{}
    show('error', 'Export failed: ' + res.status + (d?(' – '+d):'')); return;
  }
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'policies.csv';
  document.body.appendChild(a); a.click(); URL.revokeObjectURL(a.href); a.remove();
  show('ok','Exported policies.csv');
};

// Delete
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.btn-del');
  if(!btn) return;
  const id = btn.getAttribute('data-id');
  if(!confirm(`Delete policy #${id}?`)) return;
  const res = await apiFetch(`/policies/${id}`, { method:'DELETE' });
  if(res.status===204){ location.reload(); return; }
  let d=''; try{ const j=await res.json(); d=j.detail||JSON.stringify(j);}catch{}
  show('error', `Delete failed (${res.status}) ${d}`);
});

// Header sorting
document.querySelectorAll('th[data-sort]').forEach(th=>{
  th.addEventListener('click', ()=>{
    const p = new URLSearchParams(location.search);
    const curS = p.get('sort') || 'id';
    const curD = (p.get('dir') || 'desc').toLowerCase();
    const nextS = th.dataset.sort;
    const nextD = (curS===nextS && curD==='desc') ? 'asc' : 'desc';
    p.set('sort', nextS); p.set('dir', nextD);
    location.search = p.toString();
  });
});

(function markSort(){
  const p = new URLSearchParams(location.search);
  const s = (p.get('sort')||'id').toLowerCase();
  const d = (p.get('dir')||'desc').toLowerCase();
  const th = document.querySelector(`th[data-sort="${s}"]`);
  if(th) th.classList.add(d==='asc'?'asc':'desc');
})();
