import assert from 'node:assert';

// Set env vars before importing auth so it doesn't process.exit(1)
process.env.OPERATOR_PASSCODE = 'test-passcode';
process.env.OPERATOR_TOKEN_SECRET = 'test-token-secret-32-chars-long';

const { requireOperator, signToken } = await import('../src/auth.js');
const { config } = await import('../src/config.js');

function mockRes() {
  const res = {
    statusCode: 200,
    body: null,
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(data) {
      this.body = data;
      return this;
    },
  };
  return res;
}

console.log('Testing auth token cases...');

// 1. No token -> 401
{
  const req = { headers: {} };
  const res = mockRes();
  let nextCalled = false;
  requireOperator(req, res, () => { nextCalled = true; });
  assert.strictEqual(res.statusCode, 401, 'Expected 401 for no token');
  assert.strictEqual(nextCalled, false, 'next() should not be called');
  assert.strictEqual(res.body?.error?.code, 'UNAUTHORIZED');
  console.log('✅ Case 1: No token -> 401 passed');
}

// 2. Bad token -> 401
{
  const req = { headers: { authorization: 'Bearer totally.invalid.token' } };
  const res = mockRes();
  let nextCalled = false;
  requireOperator(req, res, () => { nextCalled = true; });
  assert.strictEqual(res.statusCode, 401, 'Expected 401 for bad token');
  assert.strictEqual(nextCalled, false, 'next() should not be called');
  assert.strictEqual(res.body?.error?.code, 'UNAUTHORIZED');
  console.log('✅ Case 2: Bad token -> 401 passed');
}

// 3. Expired token -> 401
{
  const expiredToken = signToken(config.operatorTokenSecret, -1000);
  const req = { headers: { authorization: `Bearer ${expiredToken}` } };
  const res = mockRes();
  let nextCalled = false;
  requireOperator(req, res, () => { nextCalled = true; });
  assert.strictEqual(res.statusCode, 401, 'Expected 401 for expired token');
  assert.strictEqual(nextCalled, false, 'next() should not be called');
  assert.strictEqual(res.body?.error?.code, 'UNAUTHORIZED');
  console.log('✅ Case 3: Expired token -> 401 passed');
}

// 4. Valid token -> 200 (next() called)
{
  const validToken = signToken(config.operatorTokenSecret, 3600000);
  const req = { headers: { authorization: `Bearer ${validToken}` } };
  const res = mockRes();
  let nextCalled = false;
  requireOperator(req, res, () => { nextCalled = true; });
  assert.strictEqual(nextCalled, true, 'next() should be called for valid token');
  assert.ok(req.operator, 'req.operator should be populated');
  console.log('✅ Case 4: Valid token -> allowed (next() called) passed');
}

console.log('\nAll 4 auth token test cases passed successfully!');
