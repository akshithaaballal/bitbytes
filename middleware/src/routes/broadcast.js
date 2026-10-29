import { Router } from 'express';
import { getNextBroadcast, getBroadcastHistory, triggerBroadcast, getBroadcastStatus } from '../agentAdapter.js';
import { requireOperator } from '../auth.js';

const router = Router();
const wrap = (fn) => (req, res, next) => fn(req, res).catch(next);

// requireOperator on all /broadcast routes
router.use('/broadcast', requireOperator);

router.get('/broadcast/next', wrap(async (req, res) => {
  const data = await getNextBroadcast();
  res.json(data);
}));

router.get('/broadcast/history', wrap(async (req, res) => {
  const data = await getBroadcastHistory();
  res.json(data);
}));

router.get('/broadcast/status/:jobId', wrap(async (req, res) => {
  const data = await getBroadcastStatus(req.params.jobId);
  res.json(data);
}));

router.post('/broadcast', wrap(async (req, res) => {
  const result = await triggerBroadcast(req.body || {});
  res.status(202).json(result);
}));

export default router;
