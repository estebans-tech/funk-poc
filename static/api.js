export function apiHeaders() {
  const k = localStorage.getItem('API_KEY');
  return k ? { 'X-API-Key': k } : {};
}
export async function apiFetch(url, opts = {}) {
  const headers = { ...(opts.headers || {}), ...apiHeaders() };
  const res = await fetch(url, { ...opts, headers });
  return res;
}
