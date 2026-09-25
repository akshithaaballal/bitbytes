import { Router } from 'express';
import { REQUEST_TYPES, createRequest, listRequests, getRequest } from '../services/requestService.js';

const router = Router();
const wrap = (fn) => (req, res, next) => fn(req, res).catch(next);

router.get('/request-types', (req, res) => res.json({ types: REQUEST_TYPES }));

router.post('/request', wrap(async (req, res) => {
  res.status(202).json({ request: await createRequest(req.body) });
}));

router.get('/requests', wrap(async (req, res) => {
  res.json({ requests: await listRequests() });
}));

router.get('/requests/:id', wrap(async (req, res) => {
  const record = await getRequest(req.params.id);
  if (!record) return res.status(404).json({ error: { code: 'NOT_FOUND', message: 'Request not found.' } });
  res.json({ request: record });
}));

export default router;
