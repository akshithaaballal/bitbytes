import { Router } from 'express';
import { getNextBroadcast, getBroadcastHistory, triggerBroadcast } from '../agentAdapter.js';

const router = Router();
const wrap = (fn) => (req, res, next) => fn(req, res).catch(next);

router.get('/broadcast/next', wrap(async (req, res) => {
  const data = await getNextBroadcast();
  res.json(data);
}));

router.get('/broadcast/history', wrap(async (req, res) => {
  const data = await getBroadcastHistory();
  res.json(data);
}));

router.post('/broadcast', wrap(async (req, res) => {
  const result = await triggerBroadcast();
  res.json(result);
}));

export default router;
