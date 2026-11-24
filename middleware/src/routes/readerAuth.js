import { Router } from 'express';
import {
  createUser,
  findUserByUsername,
  verifyPassword,
  createAccessToken,
  createSession,
  rotateSession,
  revokeSession,
  deleteUserAccount,
  exportUserData,
  checkRateLimit,
  recordFailedAttempt,
  clearFailedAttempts,
  findUserById,
} from '../services/readerAuthService.js';
import { setAuthCookies, clearAuthCookies, requireReaderAuth, verifyCsrf } from '../cookieAuth.js';
import * as agentAdapter from '../agentAdapter.js';

const router = Router();

// -------------------------------------------------------------
// POST /api/auth/signup
// -------------------------------------------------------------
router.post('/signup', verifyCsrf, async (req, res) => {
  const ip = req.ip || req.socket.remoteAddress || 'unknown';
  const ipLimit = checkRateLimit(`ip:${ip}`);
  if (!ipLimit.allowed) {
    return res.status(429).json({
      error: { code: 'RATE_LIMITED', message: `Too many attempts from this IP. Try again in ${ipLimit.waitMinutes} minutes.` },
    });
  }

  const { username, password, consent, rememberMe } = req.body || {};

  if (!consent) {
    return res.status(400).json({
      error: { code: 'CONSENT_REQUIRED', message: 'You must consent to the privacy notice (DPDP Act) to create an account.' },
    });
  }

  if (!username || typeof username !== 'string' || username.trim().length < 3 || username.trim().length > 30) {
    return res.status(400).json({
      error: { code: 'INVALID_USERNAME', message: 'Username must be between 3 and 30 characters.' },
    });
  }

  const cleanUsername = username.trim().toLowerCase();
  if (!/^[a-zA-Z0-9_.-]+$/.test(cleanUsername)) {
    return res.status(400).json({
      error: { code: 'INVALID_USERNAME', message: 'Username can only contain alphanumeric characters, hyphens, and underscores.' },
    });
  }

  if (!password || typeof password !== 'string' || password.length < 10) {
    return res.status(400).json({
      error: { code: 'INVALID_PASSWORD', message: 'Password must be at least 10 characters long.' },
    });
  }

  try {
    const user = createUser(cleanUsername, password);
    const accessToken = createAccessToken(user);
    const { rawToken } = createSession(user.id, Boolean(rememberMe));

    setAuthCookies(res, {
      accessToken,
      refreshToken: rawToken,
      rememberMe: Boolean(rememberMe),
    });

    // Asynchronously mirror backup to agent wrapper
    agentAdapter.mirrorReaderUser({
      id: user.id,
      username: user.username,
      created_at: user.created_at,
    }).catch(() => {});

    return res.status(201).json({
      ok: true,
      user: {
        id: user.id,
        username: user.username,
        created_at: user.created_at,
        preferences: JSON.parse(user.preferences || '{}'),
      },
    });
  } catch (err) {
    if (err.message === 'Username already taken') {
      return res.status(409).json({
        error: { code: 'USERNAME_TAKEN', message: 'This username is already taken. Please choose another.' },
      });
    }
    console.error('[auth/signup]', err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to create account.' } });
  }
});

// -------------------------------------------------------------
// POST /api/auth/login
// -------------------------------------------------------------
router.post('/login', verifyCsrf, async (req, res) => {
  const ip = req.ip || req.socket.remoteAddress || 'unknown';
  const { username, password, rememberMe } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({
      error: { code: 'MISSING_CREDENTIALS', message: 'Username and password are required.' },
    });
  }

  const normUser = String(username).trim().toLowerCase();
  const userRateKey = `user:${normUser}`;
  const ipRateKey = `ip:${ip}`;

  // Check rate limits on IP and username
  const userLimit = checkRateLimit(userRateKey);
  const ipLimit = checkRateLimit(ipRateKey);

  if (!userLimit.allowed || !ipLimit.allowed) {
    const wait = Math.max(userLimit.waitMinutes || 0, ipLimit.waitMinutes || 0);
    return res.status(429).json({
      error: { code: 'RATE_LIMITED', message: `Too many failed login attempts. Locked for ${wait} minutes.` },
    });
  }

  const user = findUserByUsername(normUser);
  const isValid = user ? verifyPassword(password, user.password_hash) : false;

  if (!isValid) {
    recordFailedAttempt(userRateKey);
    recordFailedAttempt(ipRateKey);
    return res.status(401).json({
      error: { code: 'INVALID_CREDENTIALS', message: 'Invalid username or password.' },
    });
  }

  // Clear failed attempt counters on successful authentication
  clearFailedAttempts(userRateKey);
  clearFailedAttempts(ipRateKey);

  const accessToken = createAccessToken(user);
  const { rawToken } = createSession(user.id, Boolean(rememberMe));

  setAuthCookies(res, {
    accessToken,
    refreshToken: rawToken,
    rememberMe: Boolean(rememberMe),
  });

  return res.json({
    ok: true,
    user: {
      id: user.id,
      username: user.username,
      created_at: user.created_at,
      preferences: JSON.parse(user.preferences || '{}'),
    },
  });
});

// -------------------------------------------------------------
// POST /api/auth/refresh
// -------------------------------------------------------------
router.post('/refresh', async (req, res) => {
  const rawToken = req.cookies?.bitbytes_refresh || req.body?.refreshToken;

  if (!rawToken) {
    return res.status(401).json({
      error: { code: 'MISSING_TOKEN', message: 'No refresh token provided.' },
    });
  }

  const result = rotateSession(rawToken);

  if (!result) {
    clearAuthCookies(res);
    return res.status(401).json({
      error: { code: 'INVALID_REFRESH_TOKEN', message: 'Session expired. Please log in again.' },
    });
  }

  if (result.reuseDetected) {
    clearAuthCookies(res);
    return res.status(401).json({
      error: { code: 'TOKEN_REUSE_DETECTED', message: 'Security alert: Refresh token reuse detected. Session revoked.' },
    });
  }

  const { user, newRawToken } = result;
  const newAccessToken = createAccessToken(user);

  setAuthCookies(res, {
    accessToken: newAccessToken,
    refreshToken: newRawToken,
    rememberMe: true,
  });

  return res.json({
    ok: true,
    user: {
      id: user.id,
      username: user.username,
      created_at: user.created_at,
      preferences: JSON.parse(user.preferences || '{}'),
    },
  });
});

// -------------------------------------------------------------
// POST /api/auth/logout
// -------------------------------------------------------------
router.post('/logout', (req, res) => {
  const rawToken = req.cookies?.bitbytes_refresh || req.body?.refreshToken;
  if (rawToken) {
    revokeSession(rawToken);
  }
  clearAuthCookies(res);
  return res.json({ ok: true, message: 'Logged out successfully.' });
});

// -------------------------------------------------------------
// GET /api/auth/me
// -------------------------------------------------------------
router.get('/me', requireReaderAuth, (req, res) => {
  const user = findUserById(req.reader.id);
  if (!user) {
    clearAuthCookies(res);
    return res.status(404).json({ error: { code: 'USER_NOT_FOUND', message: 'User not found.' } });
  }

  return res.json({
    ok: true,
    user: {
      id: user.id,
      username: user.username,
      created_at: user.created_at,
      preferences: JSON.parse(user.preferences || '{}'),
    },
  });
});

// -------------------------------------------------------------
// DELETE /api/auth/delete-account
// -------------------------------------------------------------
router.delete('/delete-account', requireReaderAuth, verifyCsrf, async (req, res) => {
  const userId = req.reader.id;
  const username = req.reader.username;

  try {
    deleteUserAccount(userId);
    clearAuthCookies(res);

    // Asynchronously notify agent wrapper of deletion
    agentAdapter.deleteReaderUser(username).catch(() => {});

    return res.json({ ok: true, message: 'Account and associated records deleted permanently.' });
  } catch (err) {
    console.error('[auth/delete-account]', err);
    return res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to delete account.' } });
  }
});

// -------------------------------------------------------------
// GET /api/auth/export-my-data
// -------------------------------------------------------------
router.get('/export-my-data', requireReaderAuth, (req, res) => {
  const data = exportUserData(req.reader.id);
  if (!data) {
    return res.status(404).json({ error: { code: 'USER_NOT_FOUND', message: 'User data not found.' } });
  }

  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', `attachment; filename="bitbytes-export-${req.reader.username}.json"`);
  return res.json(data);
});

export default router;
