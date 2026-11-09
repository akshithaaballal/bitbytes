import React from 'react';
import {
  TELEGRAM_URL,
  GITHUB_REPO_URL,
  STATS_COMMUNITY_SUBSCRIBERS,
} from '../constants.js';

export default function ProfileView({
  totalBites = 100,
  streakData = { count: 1 },
  readCount = 0,
  savedCount = 0,
  likedCount = 0,
  currentTheme = 'light',
  onToggleTheme,
  onSurpriseMe,
  onGoToOperator,
}) {
  const percentRead = Math.min(100, Math.round((readCount / Math.max(1, totalBites)) * 100));

  return (
    <section className="profile-tab-container" aria-label="Your Reading Profile">
      {/* Visitor Gamification Card */}
      <div className="visitor-card">
        <div className="visitor-card-header">
          <div className="visitor-avatar">
            <span>⚡</span>
          </div>
          <div className="visitor-identity">
            <h2 className="visitor-name">B.Tech Engineer</h2>
            <span className="visitor-badge">Anonymous Learner • Local Storage</span>
          </div>
        </div>

        {/* 4 Core Metrics */}
        <div className="visitor-metrics-grid">
          <div className="metric-box">
            <span className="metric-icon">🔥</span>
            <span className="metric-val">{streakData.count || 1} Days</span>
            <span className="metric-label">Daily Streak</span>
          </div>

          <div className="metric-box">
            <span className="metric-icon">📖</span>
            <span className="metric-val">{readCount}</span>
            <span className="metric-label">Bites Read</span>
          </div>

          <div className="metric-box">
            <span className="metric-icon">🔖</span>
            <span className="metric-val">{savedCount}</span>
            <span className="metric-label">Saved</span>
          </div>

          <div className="metric-box">
            <span className="metric-icon">❤️</span>
            <span className="metric-val">{likedCount}</span>
            <span className="metric-label">Liked</span>
          </div>
        </div>

        {/* Reading Progress Bar */}
        <div className="reading-progress-wrap">
          <div className="progress-labels">
            <span>Curriculum Progress</span>
            <strong className="progress-percent">{percentRead}% complete</strong>
          </div>
          <div className="progress-track-bar">
            <div
              className="progress-fill-bar"
              style={{ width: `${percentRead}%` }}
            />
          </div>
        </div>

        {/* "Surprise Me" Action Button */}
        <div className="surprise-me-wrap">
          <button
            type="button"
            className="btn-surprise-me"
            onClick={onSurpriseMe}
          >
            🎲 Surprise Me (Random Bite)
          </button>
        </div>
      </div>

      {/* Preferences & Settings */}
      <div className="profile-settings-card">
        <h3 className="settings-title">Preferences & Theme</h3>

        <div className="settings-row">
          <div className="settings-info">
            <span className="settings-label">Appearance</span>
            <span className="settings-desc">
              {currentTheme === 'light' ? 'Warm Risograph Paper (#F5F2EB)' : 'Warm Charcoal (#161514)'}
            </span>
          </div>
          <button
            type="button"
            className="btn-theme-toggle"
            onClick={onToggleTheme}
            aria-label="Toggle light and dark mode"
          >
            {currentTheme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
          </button>
        </div>
      </div>

      {/* Community Links */}
      <div className="profile-links-card">
        <h3 className="settings-title">Official Channels</h3>

        <div className="links-group">
          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="profile-ext-link"
          >
            <span>✈ Follow @csbites on Telegram</span>
            <span className="ext-badge">{STATS_COMMUNITY_SUBSCRIBERS} members</span>
          </a>

          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="profile-ext-link"
          >
            <span>★ Star BitBytes on GitHub</span>
            <span className="ext-arrow">↗</span>
          </a>

          <button
            type="button"
            className="profile-operator-btn"
            onClick={onGoToOperator}
          >
            <span>🔐 Operator Console (Pipeline & Broadcast)</span>
            <span className="ext-arrow">→</span>
          </button>
        </div>
      </div>

      <footer className="profile-disclaimer">
        BitBytes is 100% tracker-free. Your streaks, likes, and bookmarks exist purely inside your browser.
      </footer>
    </section>
  );
}
