import { randomUUID } from 'node:crypto';
import { config } from '../config.js';
import { submit, getResult } from '../agentAdapter.js';
import { store } from './requestStore.js';

export class ValidationError extends Error {}

// Real Cosmitude Bridge flows from BitBytesData template
export const REQUEST_TYPES = [
  { id: 'BitBytesData_DataProcessing', label: 'Data Processing', hint: 'Send data payload for processing' },
  { id: 'BitBytesData_ApplicationModule', label: 'Application Module', hint: 'Module registration and status flow' },
  { id: 'BitBytesData_ProcessingStages', label: 'Processing Stages', hint: 'Track stage initialization and progress' },
  { id: 'BitBytesData_CompletionTracking', label: 'Completion Tracking', hint: 'Log completion notes and outcomes' },
  { id: 'general', label: 'General request', hint: 'Free-form request to the agent' },
];

const MAX_MESSAGE = 2000;

function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    throw new ValidationError('Request body must be a JSON object.');
  }
  const { type, message } = body;
  if (!REQUEST_TYPES.some((t) => t.id === type)) throw new ValidationError('Choose a valid request type.');
  if (typeof message !== 'string' || !message.trim()) throw new ValidationError('Enter a message to send.');
  if (message.length > MAX_MESSAGE) {
    throw new ValidationError(`Message must be ${MAX_MESSAGE} characters or fewer.`);
  }
  return { type, message: message.trim() };
}

function touch(record, patch) {
  Object.assign(record, patch, { updatedAt: new Date().toISOString() });
}

export async function createRequest(body) {
  const { type, message } = validate(body);
  const now = new Date().toISOString();
  const record = store.add({
    id: randomUUID(), type, message,
    status: 'pending', output: null, error: null,
    createdAt: now, updatedAt: now,
  });
  console.log(`[request] ${record.id} type=${type} length=${message.length}`);
  try {
    await submit(record);
  } catch (err) {
    touch(record, { status: 'failed', error: err.message });
    throw err;
  }
  return record;
}

async function refresh(record) {
  if (record.status !== 'pending') return record;
  if (Date.now() - Date.parse(record.createdAt) > config.requestTimeoutMs) {
    touch(record, { status: 'failed', error: 'No reply from Cosmitude Bridge before the request timed out.' });
    return record;
  }
  try {
    const result = await getResult(record.id);
    if (result.status !== 'pending') touch(record, result);
  } catch (err) {
    console.warn(`[request] ${record.id} poll failed: ${err.code || 'ERROR'}`);
  }
  return record;
}

export async function listRequests() {
  const all = store.list();
  await Promise.all(all.map(refresh));
  return all;
}

export async function getRequest(id) {
  const record = store.get(id);
  return record ? refresh(record) : null;
}
