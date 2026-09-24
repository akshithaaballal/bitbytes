import 'dotenv/config';

const int = (value, fallback) => {
  const n = parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
};

export const config = {
  port: int(process.env.PORT, 4000),
  frontendOrigins: (process.env.FRONTEND_ORIGIN || 'http://localhost:5173,http://127.0.0.1:5173')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  agentUrl: (process.env.AGENT_URL || '').trim().replace(/\/+$/, ''),
  agentApiKey: process.env.AGENT_API_KEY || '',
  agentTimeoutMs: int(process.env.AGENT_TIMEOUT_MS, 10000),
  requestTimeoutMs: int(process.env.REQUEST_TIMEOUT_MS, 120000),
};
