/**
 * Safe localStorage utilities for likes, saves, reading history, streaks, and theme.
 * All operations are wrapped in try/catch to gracefully handle private browsing / sandbox restrictions.
 */

const STORAGE_KEYS = {
  LIKES: 'bitbytes_liked_posts',
  SAVES: 'bitbytes_saved_posts',
  READ_POSTS: 'bitbytes_read_posts',
  STREAK: 'bitbytes_streak_data',
  THEME: 'bitbytes_theme_mode',
};

function safeGet(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.warn(`[BitBytes] LocalStorage write failed for ${key}:`, err);
  }
}

// LIKES
export function getLikedPostIds() {
  const ids = safeGet(STORAGE_KEYS.LIKES, []);
  return new Set(Array.isArray(ids) ? ids : []);
}

export function togglePostLike(postId) {
  const set = getLikedPostIds();
  if (set.has(postId)) {
    set.delete(postId);
  } else {
    set.add(postId);
  }
  safeSet(STORAGE_KEYS.LIKES, Array.from(set));
  return set.has(postId);
}

// SAVES
export function getSavedPostIds() {
  const ids = safeGet(STORAGE_KEYS.SAVES, []);
  return new Set(Array.isArray(ids) ? ids : []);
}

export function togglePostSave(postId) {
  const set = getSavedPostIds();
  if (set.has(postId)) {
    set.delete(postId);
  } else {
    set.add(postId);
  }
  safeSet(STORAGE_KEYS.SAVES, Array.from(set));
  return set.has(postId);
}

// READ POSTS (Story Rings & Read tracking)
export function getReadPostIds() {
  const ids = safeGet(STORAGE_KEYS.READ_POSTS, []);
  return new Set(Array.isArray(ids) ? ids : []);
}

export function markPostAsRead(postId) {
  if (!postId) return;
  const set = getReadPostIds();
  if (!set.has(postId)) {
    set.add(postId);
    safeSet(STORAGE_KEYS.READ_POSTS, Array.from(set));
    // Trigger custom event so unread rings update reactively across components
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('bitbytes:post-read', { detail: { postId } }));
    }
  }
}

// STREAK TRACKING
export function getStreakData() {
  const defaultData = { count: 1, lastDate: '' };
  const data = safeGet(STORAGE_KEYS.STREAK, defaultData);
  const today = new Date().toISOString().slice(0, 10);

  if (!data.lastDate) {
    const init = { count: 1, lastDate: today };
    safeSet(STORAGE_KEYS.STREAK, init);
    return init;
  }

  if (data.lastDate === today) {
    return data;
  }

  // Calculate day difference
  const lastMs = new Date(data.lastDate).getTime();
  const todayMs = new Date(today).getTime();
  const diffDays = Math.round((todayMs - lastMs) / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    // Consecutive day
    const updated = { count: (data.count || 1) + 1, lastDate: today };
    safeSet(STORAGE_KEYS.STREAK, updated);
    return updated;
  } else if (diffDays > 1) {
    // Reset streak
    const updated = { count: 1, lastDate: today };
    safeSet(STORAGE_KEYS.STREAK, updated);
    return updated;
  }

  return data;
}

// THEME
export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.THEME);
    if (stored === 'light' || stored === 'dark') return stored;
    // Default to light (warm risograph paper) for high contrast editorial feel
    return 'light';
  } catch {
    return 'light';
  }
}

export function setStoredTheme(theme) {
  try {
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
  } catch {}
}
