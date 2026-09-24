import { Router } from 'express';
import { getStatus } from '../agentAdapter.js';

const router = Router();

router.get('/health', async (req, res) => {
  const status = await getStatus();
  res.json({ middleware: { state: 'online' }, ...status, time: new Date().toISOString() });
});

export default router;
