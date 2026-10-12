// The frontend talks ONLY to the BitBytes middleware. No secrets live here.
const BASE = import.meta.env.VITE_API_BASE || '';

async function http(path, options) {
  let res;
  try {
    res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  } catch {
    throw new Error('Cannot reach the BitBytes middleware. Check that it is running on port 4000.');
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.error?.message || `Request failed (HTTP ${res.status}).`);
  return data;
}

export const getHealth = () => http('/api/health');
export const getTypes = () => http('/api/request-types');
export const getRequests = () => http('/api/requests');
export const sendRequest = (payload) => http('/api/request', { method: 'POST', body: JSON.stringify(payload) });
export const getNextBroadcast = () => http('/api/broadcast/next');
export const triggerBroadcast = () => http('/api/broadcast', { method: 'POST', body: '{}' });
