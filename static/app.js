const msg = document.getElementById('msg');
function show(type, text){ msg.className='banner '+(type||'error'); msg.textContent=text; }

async function add(){
  const apiKey = localStorage.getItem('API_KEY');
  const body = {
    number: number.value.trim(),
    holder: holder.value.trim(),
    premium: parseFloat(premium.value),
    status: status.value.trim()
  };
  const res = await fetch('/policies', {
    method:'POST',
    headers: Object.assign({'Content-Type':'application/json'}, apiKey ? {'X-API-Key': apiKey} : {}),
    body: JSON.stringify(body)
  });
  if(res.ok){ location.reload(); return; }
  let detail=''; try{ const j=await res.json(); detail=j.detail||JSON.stringify(j);}catch{}
  if(res.status===401) show('error','Unauthorized: missing/invalid API key.');
  else if(res.status===409) show('error','Duplicate number: that policy already exists.');
  else if(res.status===422) show('error','Validation error: '+detail);
  else show('error','Error '+res.status+': '+detail);
}

async function bootstrap(){
  try{
    const h = await fetch('/health').then(r=>r.json());
    document.getElementById('health').textContent = 'health: '+(h.status||'unknown');
  }catch{ document.getElementById('health').textContent = 'health: error'; }
  const saved = localStorage.getItem('API_KEY')||'';
  apikey.value = saved;
  document.getElementById('auth').textContent = 'auth: '+(saved?'key set':'off');
}
saveKey.onclick = () => {
  const v = apikey.value.trim();
  if(v){ localStorage.setItem('API_KEY', v); show('ok','API key saved.'); }
  document.getElementById('auth').textContent = 'auth: '+(v?'key set':'off');
};
clearKey.onclick = () => {
  localStorage.removeItem('API_KEY'); apikey.value=''; document.getElementById('auth').textContent='auth: off';
  show('ok','API key cleared.');
};
window.addEventListener('DOMContentLoaded', bootstrap);
