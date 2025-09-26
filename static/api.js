export function apiHeaders() {
  const k = localStorage.getItem('API_KEY')
  const h = {}
  if (k) {
    h['X-API-Key'] = k
    h['Authorization'] = 'ApiKey ' + k // extra way, BE support
  }

  return h
}

export function withParams(url, params) {
  if (!params) return url
  const u = new URL(url, location.origin)

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) u.searchParams.set(key, String(value))
  }

  return u.toString()
}

export async function apiFetch(url, opts = {}) {
  const u = new URL(url, location.origin)
  if (u.origin !== location.origin) {
    throw new Error('Cross-origin blocked: refusing to send API key off-site')
  }
  // Default Accept, låt anroparen överskrida vid behov
  const defaultHeaders = { 'Accept': 'application/json' }
  const headers = { ...defaultHeaders, ...(opts.headers || {}), ...apiHeaders() }
  return fetch(u.toString(), { ...opts, headers })
}
