import React, { useState } from 'react';
import CalendarView from './CalendarView.jsx';
import { exportMyData } from '../services/readerAuth.js';
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
  currentUser = null,
  allPosts = [],
  onToggleTheme,
  onSurpriseMe,
  onGoToOperator,
  onLogout,
  onDeleteAccount,
  onSelectPost,
}) {
  const percentRead = Math.min(100, Math.round((readCount / Math.max(1, totalBites)) * 100));
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      await exportMyData();
    } catch (err) {
      alert('Failed to export data: ' + err.message);
    } finally {
      setExporting(false);
    }
  }

  function handleConfirmDelete() {
    if (!currentUser || confirmInput.trim() !== currentUser.username) {
      setDeleteError(`Please type "${currentUser?.username}" exactly to confirm.`);
      return;
    }
    setDeleteError('');
    onDeleteAccount && onDeleteAccount();
  }

  return (
    <section className="profile-tab-container" aria-label="Your Reading Profile">
      {/* Visitor / Reader Identity Card */}
      <div className="visitor-card">
        <div className="visitor-card-header">
          <div className="visitor-avatar">
            <span>⚡</span>
          </div>
          <div className="visitor-identity">
            <h2 className="visitor-name">
              {currentUser ? `@${currentUser.username}` : 'B.Tech Engineer'}
            </h2>
            <span className="visitor-badge">
              {currentUser ? 'Verified Reader • Cloud Sync' : 'Anonymous Learner • Local Storage'}
            </span>
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

      {/* PHASE 4: Interactive Activity Calendar */}
      <div className="profile-calendar-section">
        <h3 className="section-title">Reading Activity & Streaks</h3>
        <CalendarView allPosts={allPosts} onSelectPost={onSelectPost} />
      </div>

      {/* Account Management & Security Card */}
      {currentUser && (
        <div className="profile-account-card">
          <h3 className="settings-title">Account & Privacy (DPDP Act)</h3>
          <p className="account-card-sub">
            Your reading logs, streak history, and preferences are synchronized across your devices.
          </p>

          <div className="account-actions-row">
            <button
              type="button"
              className="btn-export-data"
              onClick={handleExport}
              disabled={exporting}
            >
              {exporting ? 'Exporting...' : '📥 Export My Data (JSON)'}
            </button>

            <button
              type="button"
              className="btn-logout-reader"
              onClick={onLogout}
            >
              Sign Out
            </button>

            <button
              type="button"
              className="btn-delete-account-trigger"
              onClick={() => { setShowDeleteModal(true); setConfirmInput(''); setDeleteError(''); }}
            >
              Delete Account
            </button>
          </div>
        </div>
      )}

      {/* Preferences & Theme */}
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

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="delete-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-dialog-title">
          <div className="delete-modal-card">
            <h3 id="delete-dialog-title" className="delete-modal-title">⚠️ Delete Your Account?</h3>
            <p className="delete-modal-text">
              This action is permanent and irreversible. All your reading history, streaks, bookmarks, and preferences will be erased from our servers in compliance with the DPDP Act.
            </p>
            <p className="delete-modal-instruction">
              To proceed, please type your username <strong>{currentUser?.username}</strong> below:
            </p>
            <input
              type="text"
              className="delete-modal-input"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder={currentUser?.username}
              autoFocus
            />
            {deleteError && <div className="delete-modal-error">{deleteError}</div>}
            <div className="delete-modal-actions">
              <button
                type="button"
                className="btn-cancel-delete"
                onClick={() => setShowDeleteModal(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-confirm-delete"
                onClick={handleConfirmDelete}
              >
                Permanently Delete Everything
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="profile-disclaimer">
        BitBytes is 100% tracker-free. Your data is encrypted and stored exclusively to empower your engineering journey.
      </footer>
    </section>
  );
}
