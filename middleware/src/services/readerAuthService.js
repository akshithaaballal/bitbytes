import { scryptSync, randomBytes, timingSafeEqual, createHmac, createHash } from 'node:crypto';
import { db } from '../db.js';
import { config } from '../config.js';

const ACCESS_TOKEN_TTL_MS = 15 * 60 * 1000; // 15 minutes
const REFRESH_TOKEN_TTL_PERSISTENT_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const REFRESH_TOKEN_TTL_SESSION_MS = 24 * 60 * 60 * 1000; // 1 day fallback for session
const MAX_FAILED_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 minutes

const JWT_SECRET = process.env.USER_TOKEN_SECRET || config.operatorTokenSecret || 'bitbytes-reader-secret-key-32chars';

// -------------------------------------------------------------
// 1. Password Hashing (scrypt + timingSafeEqual)
// -------------------------------------------------------------
export function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const derived = scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${derived}`;
}

export function verifyPassword(password, stored) {
  if (!stored || !stored.includes(':')) return false;
  const [salt, hash] = stored.split(':');
  const derived = scryptSync(password, salt, 64);
  const hashBuf = Buffer.from(hash, 'hex');
  if (derived.length !== hashBuf.length) return false;
  return timingSafeEqual(derived, hashBuf);
}

// -------------------------------------------------------------
// 2. Token Generation & Verification (Access Token)
// -------------------------------------------------------------
export function createAccessToken(user) {
  const payload = {
    sub: user.id,
    username: user.username,
    exp: Date.now() + ACCESS_TOKEN_TTL_MS,
  };
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = createHmac('sha256', JWT_SECRET).update(body).digest('base64url');
  return `${body}.${sig}`;
}

export function verifyAccessToken(token) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;
  const [body, sig] = parts;
  const expectedSig = createHmac('sha256', JWT_SECRET).update(body).digest('base64url');
  if (sig.length !== expectedSig.length) return null;
  if (!timingSafeEqual(Buffer.from(sig), Buffer.from(expectedSig))) return null;

  try {
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf-8'));
    if (payload.exp && Date.now() > payload.exp) {
      return null; // Expired
    }
    return payload;
  } catch {
    return null;
  }
}

// -------------------------------------------------------------
// 3. Refresh Token Generation, Rotation & Reuse Detection
// -------------------------------------------------------------
export function generateRefreshToken() {
  return randomBytes(32).toString('hex');
}

export function hashRefreshToken(rawToken) {
  return createHash('sha256').update(rawToken).digest('hex');
}

export function createSession(userId, rememberMe) {
  const rawToken = generateRefreshToken();
  const tokenHash = hashRefreshToken(rawToken);
  const sessionId = randomBytes(16).toString('hex');
  const familyId = randomBytes(16).toString('hex');
  const ttl = rememberMe ? REFRESH_TOKEN_TTL_PERSISTENT_MS : REFRESH_TOKEN_TTL_SESSION_MS;
  const expiresAt = new Date(Date.now() + ttl).toISOString();
  const now = new Date().toISOString();

  const stmt = db.prepare(`
    INSERT INTO reader_sessions (id, user_id, token_hash, family_id, is_revoked, expires_at, created_at)
    VALUES (?, ?, ?, ?, 0, ?, ?)
  `);
  stmt.run(sessionId, userId, tokenHash, familyId, expiresAt, now);

  return { rawToken, expiresAt, rememberMe };
}

export function rotateSession(rawToken) {
  if (!rawToken) return null;
  const tokenHash = hashRefreshToken(rawToken);

  const session = db.prepare('SELECT * FROM reader_sessions WHERE token_hash = ?').get(tokenHash);

  if (!session) {
    return null;
  }

  // Token reuse detected! Revoke the whole token family
  if (session.is_revoked === 1) {
    console.warn(`[Security Alert] Refresh token reuse detected for family ${session.family_id}. Revoking family.`);
    db.prepare('UPDATE reader_sessions SET is_revoked = 1 WHERE family_id = ?').run(session.family_id);
    return { reuseDetected: true };
  }

  // Check expiry
  if (new Date(session.expires_at).getTime() < Date.now()) {
    db.prepare('UPDATE reader_sessions SET is_revoked = 1 WHERE id = ?').run(session.id);
    return null;
  }

  // Revoke current token
  db.prepare('UPDATE reader_sessions SET is_revoked = 1 WHERE id = ?').run(session.id);

  // Issue new token in the same family
  const newRawToken = generateRefreshToken();
  const newTokenHash = hashRefreshToken(newRawToken);
  const newSessionId = randomBytes(16).toString('hex');
  const ttl = REFRESH_TOKEN_TTL_PERSISTENT_MS;
  const newExpiresAt = new Date(Date.now() + ttl).toISOString();
  const now = new Date().toISOString();

  db.prepare(`
    INSERT INTO reader_sessions (id, user_id, token_hash, family_id, is_revoked, expires_at, created_at)
    VALUES (?, ?, ?, ?, 0, ?, ?)
  `).run(newSessionId, session.user_id, newTokenHash, session.family_id, newExpiresAt, now);

  const user = db.prepare('SELECT id, username, created_at, preferences FROM readers WHERE id = ?').get(session.user_id);
  if (!user) return null;

  return {
    user,
    newRawToken,
    expiresAt: newExpiresAt,
  };
}

export function revokeSession(rawToken) {
  if (!rawToken) return;
  const tokenHash = hashRefreshToken(rawToken);
  db.prepare('UPDATE reader_sessions SET is_revoked = 1 WHERE token_hash = ?').run(tokenHash);
}

// -------------------------------------------------------------
// 4. Rate Limiting & Temporary Lockout
// -------------------------------------------------------------
export function checkRateLimit(key) {
  const now = Date.now();
  const row = db.prepare('SELECT * FROM login_attempts WHERE key = ?').get(key);

  if (!row) {
    return { allowed: true, remaining: MAX_FAILED_ATTEMPTS };
  }

  if (row.locked_until) {
    const lockedUntilTime = new Date(row.locked_until).getTime();
    if (now < lockedUntilTime) {
      const waitMinutes = Math.ceil((lockedUntilTime - now) / 60000);
      return { allowed: false, waitMinutes };
    } else {
      // Lockout expired, reset
      db.prepare('DELETE FROM login_attempts WHERE key = ?').run(key);
      return { allowed: true, remaining: MAX_FAILED_ATTEMPTS };
    }
  }

  return { allowed: true, remaining: Math.max(0, MAX_FAILED_ATTEMPTS - row.failed_count) };
}

export function recordFailedAttempt(key) {
  const now = new Date();
  const row = db.prepare('SELECT * FROM login_attempts WHERE key = ?').get(key);

  if (!row) {
    db.prepare('INSERT INTO login_attempts (key, failed_count, last_attempt) VALUES (?, 1, ?)').run(key, now.toISOString());
    return;
  }

  const newCount = row.failed_count + 1;
  let lockedUntil = null;
  if (newCount >= MAX_FAILED_ATTEMPTS) {
    lockedUntil = new Date(Date.now() + LOCKOUT_DURATION_MS).toISOString();
  }

  db.prepare('UPDATE login_attempts SET failed_count = ?, locked_until = ?, last_attempt = ? WHERE key = ?').run(
    newCount,
    lockedUntil,
    now.toISOString(),
    key
  );
}

export function clearFailedAttempts(key) {
  db.prepare('DELETE FROM login_attempts WHERE key = ?').run(key);
}

// -------------------------------------------------------------
// 5. User Operations
// -------------------------------------------------------------
export function findUserByUsername(username) {
  if (!username || typeof username !== 'string') return undefined;
  const clean = username.trim().toLowerCase();
  try {
    const row = db.prepare('SELECT id, username, password_hash, created_at, updated_at, preferences FROM readers WHERE LOWER(username) = ?').get(clean);
    if (!row || typeof row !== 'object' || !row.id || !row.username) return undefined;
    if (String(row.username).toLowerCase() !== clean) return undefined;
    return row;
  } catch (err) {
    console.error('[readerAuthService] findUserByUsername error:', err);
    return undefined;
  }
}

export function findUserById(id) {
  if (!id || typeof id !== 'string') return undefined;
  try {
    const row = db.prepare('SELECT id, username, created_at, preferences FROM readers WHERE id = ?').get(id.trim());
    if (!row || typeof row !== 'object' || !row.id) return undefined;
    return row;
  } catch (err) {
    console.error('[readerAuthService] findUserById error:', err);
    return undefined;
  }
}

export function createUser(username, password) {
  if (!username || typeof username !== 'string') {
    throw new Error('Invalid username');
  }
  const clean = username.trim().toLowerCase();
  const existing = findUserByUsername(clean);
  if (existing) {
    throw new Error('Username already taken');
  }

  const id = randomBytes(16).toString('hex');
  const passwordHash = hashPassword(password);
  const now = new Date().toISOString();
  const defaultPrefs = JSON.stringify({ theme: 'dark', timezone: 'Asia/Kolkata' });

  db.prepare(`
    INSERT INTO readers (id, username, password_hash, created_at, updated_at, preferences)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(id, clean, passwordHash, now, now, defaultPrefs);

  return { id, username: clean, created_at: now, preferences: defaultPrefs };
}

export function deleteUserAccount(userId) {
  // Cascades to sessions and progress via foreign keys
  db.prepare('DELETE FROM readers WHERE id = ?').run(userId);
}

export function exportUserData(userId) {
  const user = findUserById(userId);
  if (!user) return null;

  const progress = db.prepare('SELECT post_id, type, timestamp, tz, created_at FROM reader_progress WHERE user_id = ?').all(userId);

  return {
    user: {
      id: user.id,
      username: user.username,
      created_at: user.created_at,
      preferences: JSON.parse(user.preferences || '{}'),
    },
    activity_count: progress.length,
    activity_events: progress,
    export_generated_at: new Date().toISOString(),
  };
}
