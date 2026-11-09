import React, { useState, useEffect } from 'react';
import {
  TELEGRAM_URL,
  TELEGRAM_CHANNEL_HANDLE,
  STATS_COMMUNITY_SUBSCRIBERS,
  DISPATCH_CADENCE,
  LAUNCH_DATE_ISO,
  HIGHLIGHTS,
} from '../constants.js';

export default function ProfileHero({
  totalBites = 100,
  onSelectHighlight,
}) {
  const [copySuccess, setCopySuccess] = useState(false);
  const [showQrPopover, setShowQrPopover] = useState(false);
  const [countdownStr, setCountdownStr] = useState('00:00:00');

  // Calculate real days running from launch date
  const daysRunning = Math.max(
    1,
    Math.floor((Date.now() - new Date(LAUNCH_DATE_ISO).getTime()) / (1000 * 60 * 60 * 24))
  );

  // Live ticking countdown to next drop (8:30 AM or 8:30 PM Indian Standard Time, UTC+5:30)
  useEffect(() => {
    function updateCountdown() {
      const now = new Date();
      // Current UTC in ms
      const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
      // Current IST in ms (UTC + 5.5 hours)
      const istOffsetMs = 5.5 * 3600000;
      const istDate = new Date(utcMs + istOffsetMs);

      // Target drop 1: 08:30:00 today IST
      const dropMorning = new Date(istDate);
      dropMorning.setHours(8, 30, 0, 0);

      // Target drop 2: 20:30:00 today IST
      const dropEvening = new Date(istDate);
      dropEvening.setHours(20, 30, 0, 0);

      let targetDrop;
      if (istDate < dropMorning) {
        targetDrop = dropMorning;
      } else if (istDate < dropEvening) {
        targetDrop = dropEvening;
      } else {
        // Next drop is tomorrow morning
        targetDrop = new Date(dropMorning);
        targetDrop.setDate(targetDrop.getDate() + 1);
      }

      const diffMs = Math.max(0, targetDrop.getTime() - istDate.getTime());
      const hours = Math.floor(diffMs / 3600000);
      const mins = Math.floor((diffMs % 3600000) / 60000);
      const secs = Math.floor((diffMs % 60000) / 1000);

      const pad = (n) => String(n).padStart(2, '0');
      setCountdownStr(`${pad(hours)}:${pad(mins)}:${pad(secs)}`);
    }

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, []);

  async function handleCopyChannelLink() {
    try {
      await navigator.clipboard.writeText(TELEGRAM_URL);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch {}
  }

  return (
    <header className="profile-hero-section">
      <div className="profile-hero-top">
        {/* Profile Avatar with signature neo-brutalist ink ring */}
        <div className="profile-avatar-outer">
          <div className="profile-avatar-inner">
            <span className="profile-avatar-glyph">⚡</span>
          </div>
        </div>

        {/* Profile Identity & Stats */}
        <div className="profile-info-column">
          <div className="profile-handle-row">
            <h1 className="profile-handle">csbites</h1>
            <span className="profile-verified-badge" title="Official Telegram Community">
              ✓
            </span>
          </div>

          {/* Real stats row (only real numbers) */}
          <div className="profile-stats-row">
            <div className="stat-item">
              <span className="stat-num">{totalBites}</span>
              <span className="stat-label">bites</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">{daysRunning}+</span>
              <span className="stat-label">days running</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">{STATS_COMMUNITY_SUBSCRIBERS}</span>
              <span className="stat-label">students</span>
            </div>
          </div>
        </div>
      </div>

      {/* Human Bio (casual, no buzzwords) */}
      <div className="profile-bio-box">
        <p className="profile-bio-text">
          Bite-sized CS and systems engineering mental models, dropped twice daily.
          Zero corporate fluff — designed for engineering students scrolling between lectures.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="profile-actions-bar">
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-primary-follow"
        >
          Follow on Telegram ✈
        </a>

        <button
          type="button"
          className="btn-secondary-copy"
          onClick={handleCopyChannelLink}
        >
          {copySuccess ? '✓ Copied' : 'Copy link'}
        </button>

        {/* Desktop QR Scan Button (hidden on mobile) */}
        <button
          type="button"
          className="btn-desktop-scan"
          onClick={() => setShowQrPopover(!showQrPopover)}
          aria-label="Scan QR code to read on phone"
        >
          Scan
        </button>
      </div>

      {/* Desktop QR Popover */}
      {showQrPopover && (
        <div className="qr-popover-card">
          <div className="qr-popover-header">
            <span>Scan to read on your phone</span>
            <button
              type="button"
              className="qr-close-btn"
              onClick={() => setShowQrPopover(false)}
            >
              ✕
            </button>
          </div>
          <img
            src={`${import.meta.env.BASE_URL}telegram_qr_official.png`}
            alt="Telegram Channel QR Code"
            className="qr-popover-image"
            width="140"
            height="140"
          />
          <span className="qr-popover-sub">t.me/csbites</span>
        </div>
      )}

      {/* Live Drop Schedule Banner */}
      <div className="drop-schedule-banner">
        <span className="cadence-label">{DISPATCH_CADENCE}</span>
        <span className="schedule-divider">•</span>
        <span className="countdown-pill">
          next drop in <strong className="countdown-timer">{countdownStr}</strong>
        </span>
      </div>

      {/* Pinned Story Highlights */}
      <div className="highlights-row-strip" aria-label="Pinned Collections">
        {HIGHLIGHTS.map((h) => (
          <button
            key={h.id}
            type="button"
            className="highlight-item-btn"
            onClick={() => onSelectHighlight(h)}
          >
            <div
              className="highlight-ring"
              style={{ borderColor: h.color }}
            >
              <span className="highlight-icon">{h.icon}</span>
            </div>
            <span className="highlight-title">{h.title}</span>
          </button>
        ))}
      </div>
    </header>
  );
}
