import express from 'express';
import cors from 'cors';
import { config } from './config.js';
import { AgentError } from './agentAdapter.js';
import { ValidationError } from './services/requestService.js';
import healthRoutes from './routes/health.js';
import requestRoutes from './routes/requests.js';
import broadcastRoutes from './routes/broadcast.js';

const app = express();

app.use(cors({ origin: config.frontendOrigins }));
app.use(express.json({ limit: '16kb' }));
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => console.log(`${req.method} ${req.path} ${res.statusCode} ${Date.now() - start}ms`));
  next();
});

app.use('/api', healthRoutes);
app.use('/api', requestRoutes);
app.use('/api', broadcastRoutes);
app.use('/api', (req, res) => res.status(404).json({ error: { code: 'NOT_FOUND', message: 'Unknown route.' } }));

// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  const send = (status, code, message) => res.status(status).json({ error: { code, message } });
  if (err instanceof ValidationError) return send(400, 'INVALID_REQUEST', err.message);
  if (err.type === 'entity.parse.failed') return send(400, 'INVALID_JSON', 'Request body is not valid JSON.');
  if (err.type === 'entity.too.large') return send(413, 'TOO_LARGE', 'Request body is too large.');
  if (err instanceof AgentError) {
    console.error(`[agent] ${err.code}: ${err.message}`);
    return send(err.status, err.code, err.message);
  }
  console.error(`[server] unexpected error: ${err.message}`);
  return send(500, 'INTERNAL_ERROR', 'Something went wrong in the middleware.');
});

app.listen(config.port, () => {
  console.log(`BitBytes middleware listening on http://localhost:${config.port}`);
  console.log(config.agentUrl ? 'Agent adapter: AGENT_URL is set' : 'Agent adapter: AGENT_URL is empty (not configured)');
});
