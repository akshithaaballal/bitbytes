import React from 'react';
import { TRACK_CONFIG } from '../constants.js';

/**
 * StoryAvatar with a signature segmented SVG ring where the segment count
 * equals the number of bites in that track (or unread count).
 * Unread = bright track color with bold stroke; All read = faded/grey.
 */
export function StoryAvatar({
  trackName,
  config,
  totalBites = 1,
  unreadCount = 0,
  onClick,
}) {
  const isUnread = unreadCount > 0;
  const segments = Math.max(2, Math.min(18, totalBites));
  const radius = 34;
  const circumference = 2 * Math.PI * radius; // ~213.6
  const gap = 3;
  const dashLength = circumference / segments - gap;

  return (
    <button
      type="button"
      className="story-avatar-btn"
      onClick={onClick}
      aria-label={`Open story for ${config.label} (${unreadCount} unread)`}
    >
      <div className="story-ring-wrapper">
        <svg
          className="story-ring-svg"
          viewBox="0 0 76 76"
          width="68"
          height="68"
          aria-hidden="true"
        >
          {/* Background circle track */}
          <circle
            cx="38"
            cy="38"
            r={radius}
            fill="none"
            stroke="var(--story-ring-bg, #2E2C28)"
            strokeWidth="2.5"
          />
          {/* Segmented active ring */}
          <circle
            cx="38"
            cy="38"
            r={radius}
            fill="none"
            stroke={isUnread ? config.color : 'var(--text-muted, #7E7C74)'}
            strokeWidth={isUnread ? '3.5' : '2'}
            strokeDasharray={`${dashLength} ${gap}`}
            strokeLinecap="round"
            transform="rotate(-90 38 38)"
            opacity={isUnread ? '1' : '0.4'}
          />
        </svg>

        {/* Center circular badge with track short code */}
        <div
          className="story-inner-badge"
          style={{
            borderColor: isUnread ? config.color : 'var(--border, #2E2C28)',
            backgroundColor: isUnread ? config.bgTint : 'var(--bg-surface-secondary, #201F1D)',
          }}
        >
          <span
            className="story-badge-text"
            style={{ color: isUnread ? config.color : 'var(--text-secondary, #B0ADA6)' }}
          >
            {config.shortLabel.slice(0, 3).toUpperCase()}
          </span>
        </div>

        {/* Unread count sticker pill */}
        {isUnread && (
          <span
            className="story-unread-pill"
            style={{ backgroundColor: config.color }}
          >
            {unreadCount}
          </span>
        )}
      </div>

      <span className="story-track-label">{config.shortLabel}</span>
    </button>
  );
}

export default function StoriesRow({
  tracksMetadata = [],
  onSelectTrackStory,
}) {
  return (
    <section className="stories-row-container" aria-label="Stories by track">
      <div className="stories-scroll-strip">
        {tracksMetadata.map(({ trackName, config, totalBites, unreadCount }, idx) => (
          <StoryAvatar
            key={trackName}
            trackName={trackName}
            config={config}
            totalBites={totalBites}
            unreadCount={unreadCount}
            onClick={() => onSelectTrackStory(trackName, idx)}
          />
        ))}
      </div>
    </section>
  );
}
