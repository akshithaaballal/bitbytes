// All communication with the Cosmitude Agent lives in this file.
import { config } from './config.js';

export class AgentError extends Error {
  constructor(message, status = 502, code = 'AGENT_ERROR') {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function call(method, path, body, timeoutMs = config.agentTimeoutMs) {
  if (!config.agentUrl) {
    throw new AgentError(
      'Cosmitude Agent adapter is not configured yet. Set AGENT_URL in middleware/.env.',
      503,
      'AGENT_NOT_CONFIGURED',
    );
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers = {
      'Content-Type': 'application/json',
      'X-Agent-Key': config.agentApiKey || '',
    };
    const res = await fetch(config.agentUrl + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const msg = errBody.error || `Cosmitude Agent returned an error (HTTP ${res.status}).`;
      throw new AgentError(msg, res.status, res.status === 409 ? 'AGENT_BUSY' : 'AGENT_ERROR');
    }
    return await res.json().catch(() => ({}));
  } catch (err) {
    if (err instanceof AgentError) throw err;
    if (err.name === 'AbortError') {
      throw new AgentError('Cosmitude Agent timed out.', 504, 'AGENT_TIMEOUT');
    }
    throw new AgentError('Cosmitude Agent is unavailable.', 503, 'AGENT_UNAVAILABLE');
  } finally {
    clearTimeout(timer);
  }
}

export async function getStatus() {
  if (!config.agentUrl) {
    return { agent: { state: 'unconfigured' }, bridge: { state: 'unknown' } };
  }
  try {
    const h = await call('GET', '/health');
    const bridge =
      h.bridgeConnected === true ? 'connected' : h.bridgeConnected === false ? 'disconnected' : 'unknown';
    return { agent: { state: 'online' }, bridge: { state: bridge } };
  } catch {
    return { agent: { state: 'offline' }, bridge: { state: 'unknown' } };
  }
}

export async function submit({ id, type, message }) {
  await call('POST', '/requests', { id, type, message });
}

export async function getResult(id) {
  const raw = await call('GET', `/requests/${encodeURIComponent(id)}`);
  const status = ['pending', 'completed', 'failed'].includes(raw.status) ? raw.status : 'pending';
  return {
    status,
    output: raw.output ?? null,
    error: status === 'failed' ? String(raw.error || 'The agent reported a failure.') : null,
  };
}

export async function getNextBroadcast() {
  return await call('GET', '/broadcast/next');
}

export async function getBroadcastHistory() {
  return await call('GET', '/broadcast/history');
}

export async function triggerBroadcast(options = {}) {
  return await call('POST', '/broadcast', options, 60000);
}

export async function getBroadcastStatus(jobId) {
  return await call('GET', `/broadcast/status/${encodeURIComponent(jobId)}`);
}
