import { randomBytes } from 'node:crypto';
import { db } from '../db.js';

export const ACTIVITY_QUALIFYING_CRITERIA = 'Finishing a lesson (read event) or viewing a story slide';

export function recordEvents(userId, events) {
  if (!Array.isArray(events) || events.length === 0) return { inserted: 0 };

  const insertStmt = db.prepare(`
    INSERT INTO reader_progress (id, user_id, post_id, type, timestamp, tz, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(user_id, post_id, type) DO UPDATE SET timestamp = excluded.timestamp
  `);

  let inserted = 0;
  const now = new Date().toISOString();

  // Cap batch size to 100 for security and performance
  const batch = events.slice(0, 100);

  for (const ev of batch) {
    if (!ev || !ev.postId || !['read', 'like', 'save'].includes(ev.type)) {
      continue;
    }
    const id = ev.id || randomBytes(16).toString('hex');
    const timestamp = ev.timestamp || now;
    const tz = ev.tz || 'Asia/Kolkata';

    insertStmt.run(id, userId, ev.postId, ev.type, timestamp, tz, now);
    inserted++;
  }

  return { inserted };
}

export function getUserProgress(userId) {
  const user = db.prepare('SELECT preferences FROM readers WHERE id = ?').get(userId);
  const rows = db.prepare('SELECT post_id, type, timestamp, tz FROM reader_progress WHERE user_id = ? ORDER BY timestamp DESC').all(userId);

  const likes = new Set();
  const saves = new Set();
  const readPostIds = new Set();
  const activityByDate = {}; // 'YYYY-MM-DD' -> count of read events

  let tz = 'Asia/Kolkata';
  try {
    const prefs = JSON.parse(user?.preferences || '{}');
    if (prefs.timezone) tz = prefs.timezone;
  } catch {}

  for (const r of rows) {
    if (r.type === 'like') likes.add(r.post_id);
    if (r.type === 'save') saves.add(r.post_id);
    if (r.type === 'read') {
      readPostIds.add(r.post_id);

      // Convert timestamp to user's local date string YYYY-MM-DD
      try {
        const d = new Date(r.timestamp);
        const dateStr = d.toLocaleDateString('en-CA', { timeZone: tz }); // 'YYYY-MM-DD'
        activityByDate[dateStr] = (activityByDate[dateStr] || 0) + 1;
      } catch {
        const dateStr = r.timestamp.slice(0, 10);
        activityByDate[dateStr] = (activityByDate[dateStr] || 0) + 1;
      }
    }
  }

  // Calculate streaks
  const { currentStreak, longestStreak } = calculateStreaks(activityByDate, tz);

  return {
    likes: Array.from(likes),
    saves: Array.from(saves),
    readPostIds: Array.from(readPostIds),
    totalReads: readPostIds.size,
    activityByDate,
    currentStreak,
    longestStreak,
    preferences: JSON.parse(user?.preferences || '{}'),
    qualifyingRule: ACTIVITY_QUALIFYING_CRITERIA,
  };
}

export function updateUserPreferences(userId, newPrefs) {
  const current = db.prepare('SELECT preferences FROM readers WHERE id = ?').get(userId);
  let merged = {};
  try {
    merged = JSON.parse(current?.preferences || '{}');
  } catch {}

  if (typeof newPrefs === 'object' && newPrefs !== null) {
    if (newPrefs.theme) merged.theme = newPrefs.theme;
    if (newPrefs.timezone) merged.timezone = newPrefs.timezone;
  }

  const updatedStr = JSON.stringify(merged);
  db.prepare('UPDATE readers SET preferences = ?, updated_at = ? WHERE id = ?').run(
    updatedStr,
    new Date().toISOString(),
    userId
  );
  return merged;
}

export function calculateStreaks(activityByDate, tz = 'Asia/Kolkata') {
  const dates = Object.keys(activityByDate).filter(d => activityByDate[d] > 0).sort();
  if (dates.length === 0) return { currentStreak: 0, longestStreak: 0 };

  const activeSet = new Set(dates);
  const now = new Date();
  const todayStr = now.toLocaleDateString('en-CA', { timeZone: tz });

  // Calculate yesterday in user tz
  const yest = new Date(now.getTime() - 86400000);
  const yestStr = yest.toLocaleDateString('en-CA', { timeZone: tz });

  // Current streak calculation
  let currentStreak = 0;
  let checkDate = new Date();
  if (!activeSet.has(todayStr)) {
    // If haven't read today, check if yesterday was active
    if (activeSet.has(yestStr)) {
      checkDate = yest;
    } else {
      checkDate = null;
    }
  }

  if (checkDate) {
    let curr = new Date(checkDate);
    while (true) {
      const s = curr.toLocaleDateString('en-CA', { timeZone: tz });
      if (activeSet.has(s)) {
        currentStreak++;
        curr = new Date(curr.getTime() - 86400000);
      } else {
        break;
      }
    }
  }

  // Longest streak calculation
  let longestStreak = 0;
  let running = 0;
  let prevDate = null;

  for (const dateStr of dates) {
    const curDate = new Date(dateStr + 'T12:00:00Z');
    if (!prevDate) {
      running = 1;
    } else {
      const diffDays = Math.round((curDate.getTime() - prevDate.getTime()) / 86400000);
      if (diffDays === 1) {
        running++;
      } else {
        running = 1;
      }
    }
    if (running > longestStreak) longestStreak = running;
    prevDate = curDate;
  }

  return { currentStreak, longestStreak: Math.max(longestStreak, currentStreak) };
}
