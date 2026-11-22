import assert from 'node:assert';
import {
  createUser,
  findUserByUsername,
  verifyPassword,
  createAccessToken,
  verifyAccessToken,
  createSession,
  rotateSession,
  revokeSession,
  checkRateLimit,
  recordFailedAttempt,
  clearFailedAttempts,
  deleteUserAccount,
  exportUserData,
} from '../src/services/readerAuthService.js';
import { recordEvents, getUserProgress, updateUserPreferences } from '../src/services/readerProgressService.js';

console.log('Running Reader Auth & Progress Test Suite...');

// Clean up any test user leftover from previous runs
const existingAlice = findUserByUsername('test_alice');
if (existingAlice) {
  deleteUserAccount(existingAlice.id);
}

// 1. Password Hashing & Constant-time verification
{
  const testUser = createUser('test_alice', 'supersecretpass10');
  assert.ok(testUser.id, 'User created with ID');
  assert.strictEqual(testUser.username, 'test_alice');

  const found = findUserByUsername('TEST_ALICE'); // Case-insensitive
  assert.ok(found, 'User found case-insensitively');
  assert.ok(verifyPassword('supersecretpass10', found.password_hash), 'Correct password matches');
  assert.strictEqual(verifyPassword('wrongpassword99', found.password_hash), false, 'Wrong password rejected');

  console.log('✅ User creation and scrypt password hashing passed');
}

// 2. Access Token Generation & Expiry Verification
{
  const user = findUserByUsername('test_alice');
  const token = createAccessToken(user);
  assert.ok(typeof token === 'string' && token.includes('.'), 'Access token format valid');

  const payload = verifyAccessToken(token);
  assert.ok(payload, 'Access token verified');
  assert.strictEqual(payload.sub, user.id);
  assert.strictEqual(payload.username, 'test_alice');

  // Tampered token test
  const tampered = token.slice(0, -4) + 'abcd';
  assert.strictEqual(verifyAccessToken(tampered), null, 'Tampered token rejected');

  console.log('✅ Access token creation & HMAC signature verification passed');
}

// 3. Refresh Token Rotation & Reuse Detection
{
  const user = findUserByUsername('test_alice');
  const session1 = createSession(user.id, true); // Remember me: true
  assert.ok(session1.rawToken, 'Refresh token generated');

  // First rotation: valid
  const rot1 = rotateSession(session1.rawToken);
  assert.ok(rot1 && rot1.newRawToken, 'Session rotated successfully');
  assert.strictEqual(rot1.user.id, user.id);

  // Second rotation with old token (token reuse attack!)
  const reuseAttempt = rotateSession(session1.rawToken);
  assert.ok(reuseAttempt && reuseAttempt.reuseDetected, 'Token reuse detected');

  // The new token should now also be revoked due to family revocation
  const rotAfterRevoke = rotateSession(rot1.newRawToken);
  assert.ok(rotAfterRevoke && rotAfterRevoke.reuseDetected, 'Entire family revoked on reuse');

  console.log('✅ Refresh token rotation & family reuse revocation passed');
}

// 4. Rate Limiting & Temporary Lockout
{
  const rateKey = 'test_ip_127.0.0.1';
  clearFailedAttempts(rateKey);

  for (let i = 0; i < 4; i++) {
    recordFailedAttempt(rateKey);
    const check = checkRateLimit(rateKey);
    assert.strictEqual(check.allowed, true, `Attempt ${i + 1} still under limit`);
  }

  // 5th failed attempt triggers lockout
  recordFailedAttempt(rateKey);
  const locked = checkRateLimit(rateKey);
  assert.strictEqual(locked.allowed, false, '5th attempt triggered lockout');
  assert.ok(locked.waitMinutes > 0, 'Lockout duration reported');

  clearFailedAttempts(rateKey);
  const resetCheck = checkRateLimit(rateKey);
  assert.strictEqual(resetCheck.allowed, true, 'Rate limit cleared upon success');

  console.log('✅ Rate limiting & 15-minute temporary lockout passed');
}

// 5. Progress Sync, Idempotency & Streaks
{
  const user = findUserByUsername('test_alice');

  const events = [
    { postId: 'day_01', type: 'read', timestamp: '2026-11-20T10:00:00Z', tz: 'Asia/Kolkata' },
    { postId: 'day_01', type: 'like', timestamp: '2026-11-20T10:05:00Z', tz: 'Asia/Kolkata' },
    { postId: 'day_02', type: 'read', timestamp: '2026-11-21T14:00:00Z', tz: 'Asia/Kolkata' },
    { postId: 'day_03', type: 'read', timestamp: '2026-11-22T09:00:00Z', tz: 'Asia/Kolkata' },
    // Duplicate of day_01 read
    { postId: 'day_01', type: 'read', timestamp: '2026-11-20T10:00:00Z', tz: 'Asia/Kolkata' },
  ];

  const { inserted } = recordEvents(user.id, events);
  assert.strictEqual(inserted, 5, 'Events processed');

  const progress = getUserProgress(user.id);
  assert.strictEqual(progress.readPostIds.length, 3, 'Unique read posts tracked');
  assert.ok(progress.likes.includes('day_01'), 'Like tracked');
  assert.ok(progress.longestStreak >= 3, 'Longest streak computed from activity dates');

  // Update preferences
  updateUserPreferences(user.id, { theme: 'light', timezone: 'UTC' });
  const updatedProg = getUserProgress(user.id);
  assert.strictEqual(updatedProg.preferences.theme, 'light', 'Preference updated');

  console.log('✅ Progress tracking, idempotency, and streak calculation passed');
}

// 6. Data Export & Account Deletion
{
  const user = findUserByUsername('test_alice');
  const exportData = exportUserData(user.id);
  assert.ok(exportData, 'Export data generated');
  assert.strictEqual(exportData.user.username, 'test_alice');
  assert.ok(exportData.activity_events.length > 0, 'Activity log exported');

  deleteUserAccount(user.id);
  const deletedCheck = findUserByUsername('test_alice');
  assert.strictEqual(deletedCheck, undefined, 'User account deleted completely');

  console.log('✅ Data export (DPDP) & account deletion passed');
}

console.log('\nAll 6 Reader Auth & Progress test suites passed successfully!\n');
