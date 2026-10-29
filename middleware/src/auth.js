import crypto from 'node:crypto';
import { config } from './config.js';

const loginAttempts = new Map(); // ip -> { count, resetTime }

export function checkLoginRateLimit(ip) {
  const now = Date.now();
  const record = loginAttempts.get(ip) || { count: 0, resetTime: now + 60000 };
  if (now > record.resetTime) {
    record.count = 0;
    record.resetTime = now + 60000;
  }
  record.count += 1;
  loginAttempts.set(ip, record);
  return record.count <= 5;
}

export function checkPasscode(provided, expected) {
  if (typeof provided !== 'string' || typeof expected !== 'string') return false;
  const pBuf = Buffer.from(provided);
  const eBuf = Buffer.from(expected);
  if (pBuf.length !== eBuf.length) {
    crypto.timingSafeEqual(pBuf, pBuf);
    return false;
  }
  return crypto.timingSafeEqual(pBuf, eBuf);
}

export function signToken(secret) {
  const payload = {
    exp: Date.now() + 8 * 60 * 60 * 1000, // 8 hours
    iat: Date.now(),
  };
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${sig}`;
}

export function verifyToken(token, secret) {
  if (!token || typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 2) return null;
  const [body, sig] = parts;
  const expectedSig = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  const sigBuf = Buffer.from(sig);
  const expBuf = Buffer.from(expectedSig);
  if (sigBuf.length !== expBuf.length || !crypto.timingSafeEqual(sigBuf, expBuf)) {
    return null;
  }
  try {
    const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
    if (!payload.exp || Date.now() > payload.exp) return null;
    return payload;
  } catch {
    return null;
  }
}

export function requireOperator(req, res, next) {
  const authHeader = req.headers.authorization || '';
  if (!authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: { code: 'UNAUTHORIZED', message: 'Missing or invalid Bearer token.' } });
  }
  const token = authHeader.slice(7).trim();
  const secret = config.operatorTokenSecret || config.operatorPasscode || 'bitbytes-fallback-secret';
  const payload = verifyToken(token, secret);
  if (!payload) {
    return res.status(401).json({ error: { code: 'UNAUTHORIZED', message: 'Token is invalid or expired.' } });
  }
  req.operator = payload;
  next();
}
