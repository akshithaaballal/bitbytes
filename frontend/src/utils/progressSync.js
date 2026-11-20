import { syncProgressEvents, getProgress } from '../services/readerAuth.js';
import {
  getLikedPostIds,
  getSavedPostIds,
  getReadPostIds,
  getStoredTheme,
  setStoredTheme,
} from './storage.js';

export const ACTIVITY_QUALIFYING_CRITERIA = 'Finishing a lesson (read event) or viewing a story slide';

const QUEUE_KEY = 'bitbytes_offline_event_queue';
let syncTimer = null;
let isSyncing = false;

function getQueue() {
  try {
    const raw = localStorage.getItem(QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveQueue(queue) {
  try {
    localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
  } catch {}
}

/**
 * Queues an activity event (read, like, save) and schedules a debounced batch flush
 */
export function recordActivity(postId, type) {
  if (!postId || !['read', 'like', 'save'].includes(type)) return;

  const now = new Date();
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';

  const event = {
    id: `${postId}_${type}_${now.toISOString().slice(0, 10)}_${Math.random().toString(36).slice(2, 7)}`,
    postId,
    type,
    timestamp: now.toISOString(),
    tz,
  };

  const queue = getQueue();
  queue.push(event);
  saveQueue(queue);

  // Debounced flush
  scheduleFlush();
}

export function scheduleFlush(delayMs = 2000) {
  if (syncTimer) clearTimeout(syncTimer);
  syncTimer = setTimeout(flushQueue, delayMs);
}

export async function flushQueue() {
  if (isSyncing || !navigator.onLine) return;
  const queue = getQueue();
  if (queue.length === 0) return;

  isSyncing = true;
  try {
    const batch = queue.slice(0, 100);
    const res = await syncProgressEvents(batch);
    if (res && res.ok) {
      // Remove successfully synced events from queue
      const remaining = queue.slice(batch.length);
      saveQueue(remaining);
      if (remaining.length > 0) {
        scheduleFlush(1000);
      }
    }
  } catch (err) {
    console.warn('[progressSync] Background sync delayed:', err.message);
    // Exponential backoff retry
    scheduleFlush(10000);
  } finally {
    isSyncing = false;
  }
}

/**
 * On first login, merge local offline storage with server progress data (union for sets)
 */
export async function initialSyncOnLogin() {
  try {
    const { progress } = await getProgress();
    if (!progress) return null;

    // 1. Union likes
    const localLikes = getLikedPostIds();
    progress.likes.forEach((id) => localLikes.add(id));
    localStorage.setItem('bitbytes_likes', JSON.stringify(Array.from(localLikes)));

    // 2. Union saves
    const localSaves = getSavedPostIds();
    progress.saves.forEach((id) => localSaves.add(id));
    localStorage.setItem('bitbytes_saved', JSON.stringify(Array.from(localSaves)));

    // 3. Union read posts
    const localReads = getReadPostIds();
    progress.readPostIds.forEach((id) => localReads.add(id));
    localStorage.setItem('bitbytes_read_posts', JSON.stringify(Array.from(localReads)));

    // 4. Preferences (newest-wins)
    if (progress.preferences?.theme) {
      setStoredTheme(progress.preferences.theme);
    }

    // Flush any pending events from before login
    flushQueue();

    return progress;
  } catch (err) {
    console.warn('[progressSync] Initial sync failed:', err.message);
    return null;
  }
}

// Listen for network reconnect
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    scheduleFlush(500);
  });
}
