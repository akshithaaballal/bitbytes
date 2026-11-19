import { Router } from 'express';
import { requireReaderAuth, verifyCsrf } from '../cookieAuth.js';
import {
  recordEvents,
  getUserProgress,
  updateUserPreferences,
  ACTIVITY_QUALIFYING_CRITERIA,
} from '../services/readerProgressService.js';
import * as agentAdapter from '../agentAdapter.js';

const router = Router();

// -------------------------------------------------------------
// GET /api/progress
// -------------------------------------------------------------
router.get('/', requireReaderAuth, (req, res) => {
  const userId = req.reader.id;
  try {
    const data = getUserProgress(userId);
    return res.json({ ok: true, progress: data });
  } catch (err) {
    console.error('[progress/get]', err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch progress.' } });
  }
});

// -------------------------------------------------------------
// POST /api/progress/events
// -------------------------------------------------------------
router.post('/events', requireReaderAuth, verifyCsrf, (req, res) => {
  const userId = req.reader.id;
  const { events } = req.body || {};

  if (!Array.isArray(events)) {
    return res.status(400).json({
      error: { code: 'INVALID_PAYLOAD', message: 'Payload must contain an "events" array.' },
    });
  }

  if (events.length > 200) {
    return res.status(413).json({
      error: { code: 'BATCH_TOO_LARGE', message: 'Maximum 200 events per sync batch.' },
    });
  }

  try {
    const { inserted } = recordEvents(userId, events);

    // Asynchronously mirror progress events to Agent Wrapper
    agentAdapter.mirrorReaderProgress({
      username: req.reader.username,
      events,
    }).catch(() => {});

    return res.json({ ok: true, inserted });
  } catch (err) {
    console.error('[progress/events]', err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to record events.' } });
  }
});

// -------------------------------------------------------------
// PUT /api/progress/preferences
// -------------------------------------------------------------
router.put('/preferences', requireReaderAuth, verifyCsrf, (req, res) => {
  const userId = req.reader.id;
  const { theme, timezone } = req.body || {};

  try {
    const updated = updateUserPreferences(userId, { theme, timezone });
    return res.json({ ok: true, preferences: updated });
  } catch (err) {
    console.error('[progress/preferences]', err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to update preferences.' } });
  }
});

export default router;
