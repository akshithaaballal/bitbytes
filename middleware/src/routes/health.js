import { Router } from 'express';
import { getStatus } from '../agentAdapter.js';

const router = Router();

router.get('/health', async (req, res) => {
  const status = await getStatus();
  res.json({
    ok: true,
    middleware: 'online',
    agent: status.agent.state,
    bridge: status.bridge.state,
    time: new Date().toISOString(),
  });
});

export default router;
