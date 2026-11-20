/**
 * Reader Authentication & Progress Sync API Client
 * Sends cookies with credentials: 'include' and CSRF header X-Requested-With
 */

const API_BASE = '/api';

const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'X-Requested-With': 'XMLHttpRequest',
  'X-BitBytes-Client': '1',
};

async function handleResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errorMsg = data.error?.message || data.error || `HTTP ${res.status}`;
    const err = new Error(errorMsg);
    err.code = data.error?.code || 'API_ERROR';
    err.status = res.status;
    throw err;
  }
  return data;
}

export async function signup({ username, password, consent, rememberMe }) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ username, password, consent, rememberMe }),
  });
  return handleResponse(res);
}

export async function login({ username, password, rememberMe }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ username, password, rememberMe }),
  });
  return handleResponse(res);
}

export async function logout() {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function getMe() {
  const res = await fetch(`${API_BASE}/auth/me`, {
    method: 'GET',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function deleteAccount() {
  const res = await fetch(`${API_BASE}/auth/delete-account`, {
    method: 'DELETE',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function exportMyData() {
  const res = await fetch(`${API_BASE}/auth/export-my-data`, {
    method: 'GET',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to export data');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bitbytes-export-${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function getProgress() {
  const res = await fetch(`${API_BASE}/progress`, {
    method: 'GET',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function syncProgressEvents(events) {
  if (!events || events.length === 0) return { ok: true, inserted: 0 };
  const res = await fetch(`${API_BASE}/progress/events`, {
    method: 'POST',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
    body: JSON.stringify({ events }),
  });
  return handleResponse(res);
}

export async function updatePreferences(prefs) {
  const res = await fetch(`${API_BASE}/progress/preferences`, {
    method: 'PUT',
    headers: DEFAULT_HEADERS,
    credentials: 'include',
    body: JSON.stringify(prefs),
  });
  return handleResponse(res);
}
