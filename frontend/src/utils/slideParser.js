import React from 'react';
import { normalizeTrack } from '../constants.js';

/**
 * Parses inline markdown tokens (**bold**, *bold/italic*, `code`) into React elements
 * without dangerouslySetInnerHTML, completely eliminating literal asterisks.
 */
export function renderInlineMarkdown(text) {
  if (!text || typeof text !== 'string') return '';
  const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return tokens.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      return React.createElement(
        'code',
        { key: index, className: 'inline-code' },
        part.slice(1, -1)
      );
    }
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      return React.createElement(
        'strong',
        { key: index, className: 'slide-bold' },
        part.slice(2, -2)
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
      return React.createElement(
        'strong',
        { key: index, className: 'slide-bold' },
        part.slice(1, -1)
      );
    }
    return part;
  });
}

/**
 * Strips synthetic news lead-in boilerplate ("As you might have heard recently...")
 * and returns the direct engineering mental model.
 */
export function extractCoreExplanation(summary) {
  if (!summary) return '';
  let cleaned = summary;

  // Match and strip "As you might have heard recently... Let's learn about this:"
  const coreMatch = summary.match(
    /(?:Let's learn about this:|what actually is[^\?]+\?\s*(?:Let's learn about this:)?)\s*(.*)/i
  );
  if (coreMatch && coreMatch[1] && coreMatch[1].trim().length > 30) {
    cleaned = coreMatch[1].trim();
  } else {
    cleaned = cleaned.replace(/^As you might have heard recently,[^:]*?:\s*/i, '');
    cleaned = cleaned.replace(/^Let's learn about this:\s*/i, '');
  }

  // Capitalize first character
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

/**
 * Curated conversational hooks for common technical concepts to sound like a smart senior.
 */
const CURATED_HOOKS = {
  'Kernel Space vs. User Space Protection Rings':
    "Why doesn't one crashing app freeze your entire laptop?",
  'Distributed Idempotency & Two-Phase Locking':
    "What happens if a user double-clicks 'Pay $50' on spotty 4G?",
  'LSM-Trees vs. B-Trees in High-Throughput Storage':
    'Why do databases write sequential append logs instead of updating rows in place?',
  'TCP Three-Way Handshake & SYN Floods':
    'How do two servers across the world agree on state before sending a single byte?',
  'Cache Stampede & Cache Invalidation Strategies':
    "What happens when 50,000 users request a key the millisecond it expires?",
  'Raft Consensus & Leader Election Heartbeats':
    'How do 5 servers agree on the truth when 2 of them have silently disconnected?',
  'Process Memory Layout & Context Switch Overhead':
    'What actually gets swapped in CPU registers when switching threads vs processes?',
  'Virtual Memory, Paging, and Page Faults':
    'How can an 8GB laptop run three apps that each allocate 12GB of RAM?',
  'Bloom Filters in Distributed Caches':
    'How do you check if a username is taken across 1 billion rows in under 2ms?',
  'Consistent Hashing in Distributed Key-Value Stores':
    "When a server dies in a cluster, why don't you have to rehash the entire database?",
};

export function getPostHook(post) {
  if (CURATED_HOOKS[post.title]) {
    return CURATED_HOOKS[post.title];
  }

  // If subtitle has an informative scenario
  if (post.subtitle && post.subtitle.length < 90) {
    return post.subtitle;
  }

  // Fallback to title as hook
  return `How does ${post.title} work under the hood?`;
}

/**
 * Auto-splits a post into 4-5 swipeable carousel slides:
 * 1. Hook slide: Big question / scenario + track motif
 * 2. Mental Model slide: Core explanation + visual diagram
 * 3. Deep Dive slide: Code snippet or engineering trade-offs
 * 4. Systems Complexity slide: Time/space/memory constraints + interview tip
 * 5. Source & Action slide: Source domain, Telegram discussion, share actions
 */
export function buildPostSlides(post) {
  const track = normalizeTrack(post.track);
  const hook = getPostHook(post);
  const coreText = extractCoreExplanation(post.summary);

  const slides = [];

  // SLIDE 1: HOOK / COVER
  slides.push({
    type: 'hook',
    title: post.title,
    hook: hook,
    track: track,
    readMinutes: post.read_minutes || 1,
  });

  // SLIDE 2: MENTAL MODEL / EXPLANATION
  // Max ~35 words for punchy reading
  const words = coreText.split(/\s+/);
  const explanationChunk = words.slice(0, 42).join(' ') + (words.length > 42 ? '...' : '');

  slides.push({
    type: 'mental_model',
    heading: 'The Mental Model',
    text: explanationChunk,
    track: track,
    hasDiagram: true,
  });

  // SLIDE 3: CODE SNIPPET OR ARCHITECTURAL MECHANISM
  if (post.code_snippet && post.code_snippet.trim().length > 10) {
    slides.push({
      type: 'code',
      heading: 'How It Executes',
      code: post.code_snippet,
      track: track,
    });
  } else if (Array.isArray(post.key_points) && post.key_points.length > 0) {
    slides.push({
      type: 'key_points',
      heading: 'Core Architecture',
      points: post.key_points.slice(0, 3),
      track: track,
    });
  }

  // SLIDE 4: COMPLEXITY & CONSTRAINTS
  const complexityEntries = post.complexity && typeof post.complexity === 'object'
    ? Object.entries(post.complexity).filter(([_, v]) => Boolean(v))
    : [];

  slides.push({
    type: 'complexity',
    heading: 'Systems Trade-Offs',
    complexityEntries: complexityEntries,
    interviewTip: post.interview_tip || null,
    track: track,
  });

  // SLIDE 5: SOURCE & COMMUNITY
  slides.push({
    type: 'source',
    heading: 'Source & Discussion',
    source: post.source || { domain: 'engineering-notebook', title: post.title, url: '#' },
    telegramUrl: post.telegram_url || 'https://t.me/csbites',
    track: track,
    postTitle: post.title,
  });

  return slides;
}

/**
 * Format relative time (e.g., "2h ago", "1d ago") from an ISO timestamp
 */
export function formatRelativeTime(dateStr) {
  if (!dateStr) return 'today';
  try {
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diffMs = Math.max(0, now - then);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${Math.max(1, diffMins)}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return `${Math.floor(diffDays / 7)}w ago`;
  } catch {
    return 'recently';
  }
}
