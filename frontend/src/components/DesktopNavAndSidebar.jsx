import React from 'react';
import { TELEGRAM_URL, DISPATCH_CADENCE, STATS_COMMUNITY_SUBSCRIBERS } from '../constants.js';

export function DesktopLeftRail({
  activeTab = 'feed',
  onTabChange,
  savedCount = 0,
  currentTheme = 'light',
  onToggleTheme,
  onGoToOperator,
}) {
  const navItems = [
    {
      id: 'feed',
      label: 'Home Feed',
      icon: '⌂',
    },
    {
      id: 'explore',
      label: 'Explore Grid',
      icon: '⚲',
    },
    {
      id: 'saved',
      label: 'Saved Bites',
      icon: '🔖',
      badge: savedCount > 0 ? savedCount : null,
    },
    {
      id: 'profile',
      label: 'Your Stats',
      icon: '👤',
    },
  ];

  return (
    <aside className="desktop-left-rail" aria-label="Desktop Navigation">
      {/* Brand Wordmark */}
      <div className="rail-brand-header">
        <span className="brand-logo-glyph">⚡</span>
        <span className="brand-logo-text">bitbytes</span>
      </div>

      <nav className="rail-nav-menu">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`rail-nav-link ${isActive ? 'is-active' : ''}`}
              onClick={() => onTabChange(item.id)}
            >
              <span className="rail-nav-icon">{item.icon}</span>
              <span className="rail-nav-label">{item.label}</span>
              {item.badge && <span className="rail-badge">{item.badge}</span>}
            </button>
          );
        })}
      </nav>

      {/* Primary Community Action */}
      <div className="rail-actions-box">
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-rail-telegram"
        >
          Follow on Telegram ✈
        </a>

        {/* Theme Toggle Button */}
        <button
          type="button"
          className="btn-rail-theme"
          onClick={onToggleTheme}
        >
          {currentTheme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
        </button>

        {/* Operator Login Gateway */}
        <button
          type="button"
          className="btn-rail-operator"
          onClick={onGoToOperator}
        >
          Operator Console ↗
        </button>
      </div>
    </aside>
  );
}

export function DesktopRightSidebar({
  streakData = { count: 1 },
  totalBites = 100,
  readCount = 0,
  onSurpriseMe,
}) {
  const percentRead = Math.min(100, Math.round((readCount / Math.max(1, totalBites)) * 100));

  return (
    <aside className="desktop-right-sidebar" aria-label="Reading telemetry">
      {/* Daily Streak Card */}
      <div className="sidebar-card">
        <div className="sidebar-card-title">
          <span>🔥 Daily Streak</span>
          <span className="streak-tag">ACTIVE</span>
        </div>
        <div className="streak-big-stat">
          <span className="streak-count-val">{streakData.count || 1}</span>
          <span className="streak-days-label">days in a row</span>
        </div>
        <p className="sidebar-note-text">
          Read at least one bite each day to maintain your engineering momentum.
        </p>
      </div>

      {/* Curriculum Completion */}
      <div className="sidebar-card">
        <div className="sidebar-card-title">
          <span>📖 Curriculum Progress</span>
          <span className="progress-badge">{percentRead}%</span>
        </div>
        <div className="sidebar-progress-bar">
          <div
            className="sidebar-progress-fill"
            style={{ width: `${percentRead}%` }}
          />
        </div>
        <div className="sidebar-progress-stats">
          <span>{readCount} completed</span>
          <span>{totalBites} total</span>
        </div>
      </div>

      {/* Surprise Me Widget */}
      <div className="sidebar-card surprise-widget-card">
        <div className="sidebar-card-title">
          <span>🎲 Surprise Me</span>
        </div>
        <p className="sidebar-note-text">
          Jump straight into an unread engineering concept picked at random.
        </p>
        <button
          type="button"
          className="btn-sidebar-surprise"
          onClick={onSurpriseMe}
        >
          Open Random Bite →
        </button>
      </div>

      {/* Channel QR Widget */}
      <div className="sidebar-card qr-widget-card">
        <span className="qr-widget-title">Read on your phone</span>
        <img
          src={`${import.meta.env.BASE_URL}telegram_qr_official.png`}
          alt="Telegram QR"
          className="sidebar-qr-img"
          width="110"
          height="110"
        />
        <span className="qr-widget-handle">@csbites • Telegram</span>
      </div>
    </aside>
  );
}
