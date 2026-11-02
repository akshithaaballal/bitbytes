/**
 * Shared BitBytes Platform Constants & Design Tokens
 */

export const TELEGRAM_CHANNEL_HANDLE = '@csbites';
export const TELEGRAM_URL = 'https://t.me/csbites';
export const TELEGRAM_WEB_URL = 'https://telegram.me/csbites';
export const TELEGRAM_APP_URL = 'tg://resolve?domain=csbites';
export const GITHUB_REPO_URL = 'https://github.com/akshithaaballal/bitbytes';
export const DISPATCH_CADENCE = 'New bites at 8:30 AM & 8:30 PM IST';

// Telegram community real verified stats
export const STATS_COMMUNITY_SUBSCRIBERS = '1.2k+';
export const LAUNCH_DATE_ISO = '2026-10-10T00:00:00Z';

/**
 * Normalized track metadata with signature flat color tokens and badges.
 * No generic gradients or SaaS blue-to-purple.
 */
export const TRACK_CONFIG = {
  'Operating Systems': {
    id: 'os',
    label: 'Operating Systems',
    shortLabel: 'OS',
    color: '#FF5722', // Burnt Coral / Tomato
    bgTint: 'rgba(255, 87, 34, 0.12)',
    tag: '#OS',
  },
  'Distributed Systems': {
    id: 'distributed',
    label: 'Distributed Systems',
    shortLabel: 'Distributed',
    color: '#8B5CF6', // Electric Violet
    bgTint: 'rgba(139, 92, 246, 0.12)',
    tag: '#Distributed',
  },
  'Databases & Storage': {
    id: 'databases',
    label: 'Databases & Storage',
    shortLabel: 'Databases',
    color: '#0284C7', // Cobalt Cerulean
    bgTint: 'rgba(2, 132, 199, 0.12)',
    tag: '#DBMS',
  },
  'Computer Networks': {
    id: 'networks',
    label: 'Computer Networks',
    shortLabel: 'Networks',
    color: '#10B981', // Spring Emerald
    bgTint: 'rgba(16, 185, 129, 0.12)',
    tag: '#Networks',
  },
  'DSA': {
    id: 'dsa',
    label: 'Algorithms & Data Structures',
    shortLabel: 'DSA',
    color: '#F59E0B', // Sunburst Amber
    bgTint: 'rgba(245, 158, 11, 0.12)',
    tag: '#DSA',
  },
  'AI & Machine Learning': {
    id: 'aiml',
    label: 'AI & Machine Learning',
    shortLabel: 'AI/ML',
    color: '#EC4899', // Hot Magenta
    bgTint: 'rgba(236, 72, 153, 0.12)',
    tag: '#AIML',
  },
  'System Design': {
    id: 'sysdesign',
    label: 'System Design 101',
    shortLabel: 'SysDesign',
    color: '#3B82F6', // Electric Indigo Blue
    bgTint: 'rgba(59, 130, 246, 0.12)',
    tag: '#SystemDesign',
  },
  'Weekly Puzzle': {
    id: 'puzzle',
    label: 'Weekly Recap & Puzzle',
    shortLabel: 'Puzzle',
    color: '#EF4444', // Crimson Signal
    bgTint: 'rgba(239, 68, 68, 0.12)',
    tag: '#Puzzle',
  },
  'Developer Tools': {
    id: 'devtools',
    label: 'Developer Tools & Git',
    shortLabel: 'DevTools',
    color: '#14B8A6', // Mint Teal
    bgTint: 'rgba(20, 184, 166, 0.12)',
    tag: '#Git',
  },
};

/**
 * Merges duplicate and legacy track strings into our canonical track list.
 */
export function normalizeTrack(rawTrack) {
  if (!rawTrack) return 'Operating Systems';
  const t = String(rawTrack).trim();
  if (
    t === 'Core Operating Systems' ||
    t === 'Core CS: Operating Systems' ||
    t.toLowerCase().includes('operating system')
  ) {
    return 'Operating Systems';
  }
  if (t.toLowerCase().includes('distributed')) return 'Distributed Systems';
  if (t.toLowerCase().includes('machine learning') || t.toLowerCase().includes('ai &')) {
    return 'AI & Machine Learning';
  }
  if (t.toLowerCase().includes('system design')) return 'System Design';
  if (t.toLowerCase().includes('dsa') || t.toLowerCase().includes('algorithm') || t.toLowerCase().includes('data structure')) {
    return 'DSA';
  }
  if (t.toLowerCase().includes('puzzle') || t.toLowerCase().includes('recap')) {
    return 'Weekly Puzzle';
  }
  if (t.toLowerCase().includes('database') || t.toLowerCase().includes('storage')) {
    return 'Databases & Storage';
  }
  if (t.toLowerCase().includes('network')) return 'Computer Networks';
  if (t.toLowerCase().includes('git') || t.toLowerCase().includes('tools')) {
    return 'Developer Tools';
  }
  return 'Operating Systems';
}

export function getTrackConfig(trackName) {
  const normalized = normalizeTrack(trackName);
  return (
    TRACK_CONFIG[normalized] || {
      id: 'general',
      label: normalized,
      shortLabel: normalized.slice(0, 8),
      color: '#CCFF00',
      bgTint: 'rgba(204, 255, 0, 0.12)',
      tag: `#${normalized.replace(/\s+/g, '')}`,
    }
  );
}

/**
 * Pinned story highlights under the profile header.
 */
export const HIGHLIGHTS = [
  {
    id: 'exam-mode',
    title: 'Exam Mode',
    desc: 'OS, DBMS, Networks, DSA',
    tracks: ['Operating Systems', 'Databases & Storage', 'Computer Networks', 'DSA'],
    icon: '📝',
    color: '#FF5722',
  },
  {
    id: 'interview-classics',
    title: 'Interview Classics',
    desc: 'Distributed systems & System design',
    tracks: ['Distributed Systems', 'System Design'],
    icon: '🎯',
    color: '#8B5CF6',
  },
  {
    id: 'weekend-puzzles',
    title: 'Weekend Puzzles',
    desc: 'Bit manipulation & brainteasers',
    tracks: ['Weekly Puzzle'],
    icon: '🧩',
    color: '#EF4444',
  },
  {
    id: 'beginner-friendly',
    title: 'Beginner Friendly',
    desc: 'Foundational mental models',
    tracks: ['Operating Systems', 'Developer Tools', 'DSA'],
    icon: '🌱',
    color: '#10B981',
  },
];
