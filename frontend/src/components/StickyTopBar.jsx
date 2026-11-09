import React from 'react';
import { TELEGRAM_URL } from '../constants.js';

export default function StickyTopBar({
  onLogoClick,
  currentTheme = 'light',
  onToggleTheme,
}) {
  return (
    <header className="mobile-sticky-topbar">
      <div className="topbar-inner">
        <button
          type="button"
          className="topbar-logo-btn"
          onClick={onLogoClick}
          aria-label="BitBytes Home"
        >
          <span className="logo-glyph">⚡</span>
          <span className="logo-text">bitbytes</span>
        </button>

        <div className="topbar-actions">
          <button
            type="button"
            className="topbar-theme-btn"
            onClick={onToggleTheme}
            aria-label="Toggle dark/light theme"
          >
            {currentTheme === 'light' ? '🌙' : '☀️'}
          </button>

          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="topbar-follow-btn"
          >
            Follow
          </a>
        </div>
      </div>
    </header>
  );
}
