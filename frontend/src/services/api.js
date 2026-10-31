// The frontend talks ONLY to the BitBytes middleware. No secrets live here.
const BASE = import.meta.env.VITE_API_BASE || '';

async function http(path, options = {}) {
  let res;
  const token = sessionStorage.getItem('bitbytes_operator_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  try {
    res = await fetch(BASE + path, { ...options, headers });
  } catch {
    throw new Error('Cannot reach the BitBytes middleware. Check that it is running on port 4000.');
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = data?.error?.message || `Request failed (HTTP ${res.status}).`;
    const err = new Error(msg);
    err.status = res.status;
    err.code = data?.error?.code;
    throw err;
  }
  return data;
}

export const operatorLogin = async (passcode) => {
  const data = await http('/api/operator/login', {
    method: 'POST',
    body: JSON.stringify({ passcode }),
  });
  if (data?.token) {
    sessionStorage.setItem('bitbytes_operator_token', data.token);
  }
  return data;
};

export const getHealth = () => http('/api/health');
export const getTypes = () => http('/api/request-types');
export const getRequests = () => http('/api/requests');
export const sendRequest = (payload) => http('/api/request', { method: 'POST', body: JSON.stringify(payload) });
export const getNextBroadcast = () => http('/api/broadcast/next');
export const getBroadcastHistory = () => http('/api/broadcast/history');
export const triggerBroadcast = (options = {}) => http('/api/broadcast', { method: 'POST', body: JSON.stringify(options) });
export const getBroadcastStatus = (jobId) => http(`/api/broadcast/status/${encodeURIComponent(jobId)}`);
