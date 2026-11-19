import { verifyAccessToken } from './services/readerAuthService.js';

export function parseCookies(req, res, next) {
  const header = req.headers.cookie;
  req.cookies = {};
  if (header) {
    header.split(';').forEach((part) => {
      const [key, ...vals] = part.trim().split('=');
      if (key) {
        req.cookies[key] = decodeURIComponent(vals.join('='));
      }
    });
  }
  next();
}

export function serializeCookie(name, val, options = {}) {
  let str = `${name}=${encodeURIComponent(val)}`;
  if (options.maxAge !== undefined) {
    str += `; Max-Age=${Math.floor(options.maxAge / 1000)}`;
  }
  if (options.domain) str += `; Domain=${options.domain}`;
  if (options.path) str += `; Path=${options.path}`;
  else str += '; Path=/';
  if (options.expires) str += `; Expires=${options.expires.toUTCString()}`;
  if (options.httpOnly) str += '; HttpOnly';
  if (options.secure) str += '; Secure';
  if (options.sameSite) str += `; SameSite=${options.sameSite}`;
  return str;
}

export function setAuthCookies(res, { accessToken, refreshToken, rememberMe, domain }) {
  const isProd = process.env.NODE_ENV === 'production';
  const cookieDomain = process.env.COOKIE_DOMAIN || domain || undefined;

  // 1. Access Token Cookie: short-lived (15 min)
  const accessCookie = serializeCookie('bitbytes_access', accessToken, {
    maxAge: 15 * 60 * 1000,
    httpOnly: true,
    secure: isProd,
    sameSite: 'Lax',
    domain: cookieDomain,
    path: '/',
  });

  // 2. Refresh Token Cookie: 30 days if rememberMe, else session cookie (no maxAge)
  const refreshOpts = {
    httpOnly: true,
    secure: isProd,
    sameSite: 'Lax',
    domain: cookieDomain,
    path: '/',
  };
  if (rememberMe) {
    refreshOpts.maxAge = 30 * 24 * 60 * 60 * 1000;
  }
  const refreshCookie = serializeCookie('bitbytes_refresh', refreshToken, refreshOpts);

  res.setHeader('Set-Cookie', [accessCookie, refreshCookie]);
}

export function clearAuthCookies(res, domain) {
  const isProd = process.env.NODE_ENV === 'production';
  const cookieDomain = process.env.COOKIE_DOMAIN || domain || undefined;

  const clearAccess = serializeCookie('bitbytes_access', '', {
    maxAge: 0,
    httpOnly: true,
    secure: isProd,
    sameSite: 'Lax',
    domain: cookieDomain,
    path: '/',
  });
  const clearRefresh = serializeCookie('bitbytes_refresh', '', {
    maxAge: 0,
    httpOnly: true,
    secure: isProd,
    sameSite: 'Lax',
    domain: cookieDomain,
    path: '/',
  });

  res.setHeader('Set-Cookie', [clearAccess, clearRefresh]);
}

export function requireReaderAuth(req, res, next) {
  // Check cookie first, then Authorization Bearer header
  let token = req.cookies?.bitbytes_access;
  if (!token && req.headers.authorization?.startsWith('Bearer ')) {
    token = req.headers.authorization.slice(7);
  }

  if (!token) {
    return res.status(401).json({
      error: { code: 'UNAUTHORIZED', message: 'Reader authentication required.' },
    });
  }

  const payload = verifyAccessToken(token);
  if (!payload) {
    return res.status(401).json({
      error: { code: 'TOKEN_EXPIRED', message: 'Access token expired or invalid.' },
    });
  }

  req.reader = { id: payload.sub, username: payload.username };
  next();
}

export function verifyCsrf(req, res, next) {
  // State-changing requests must include custom client header to block cross-site forms
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method)) {
    const customHeader = req.headers['x-requested-with'] || req.headers['x-bitbytes-client'];
    if (!customHeader && !req.headers.authorization) {
      return res.status(403).json({
        error: { code: 'CSRF_REJECTED', message: 'Missing CSRF verification header (X-Requested-With or X-BitBytes-Client).' },
      });
    }
  }
  next();
}
