import React, { useState } from 'react';
import { login, signup } from '../services/readerAuth.js';
import { initialSyncOnLogin } from '../utils/progressSync.js';

export default function ReaderAuthModal({ onAuthSuccess, onGoToOperator }) {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [dpdpConsent, setDpdpConsent] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setErrorMsg('');

    if (!username.trim()) {
      setErrorMsg('Please enter a username.');
      return;
    }

    if (password.length < 10) {
      setErrorMsg('Password must be at least 10 characters.');
      return;
    }

    if (mode === 'signup' && !dpdpConsent) {
      setErrorMsg('You must consent to the privacy notice to create an account.');
      return;
    }

    setLoading(true);
    try {
      let res;
      if (mode === 'signup') {
        res = await signup({
          username: username.trim(),
          password,
          consent: dpdpConsent,
          rememberMe,
        });
      } else {
        res = await login({
          username: username.trim(),
          password,
          rememberMe,
        });
      }

      if (res && res.user) {
        // Sync local storage with server
        await initialSyncOnLogin();
        onAuthSuccess(res.user);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="reader-auth-overlay" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
      <div className="reader-auth-card">
        {/* Brand Header */}
        <div className="auth-brand-header">
          <div className="auth-badge-glyph">⚡</div>
          <h2 id="auth-modal-title" className="auth-brand-title">BitBytes</h2>
          <p className="auth-brand-tagline">Daily CS mental models before your chai cools down</p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-mode-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={`auth-tab-btn ${mode === 'login' ? 'is-active' : ''}`}
            onClick={() => { setMode('login'); setErrorMsg(''); }}
          >
            Log In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'signup'}
            className={`auth-tab-btn ${mode === 'signup' ? 'is-active' : ''}`}
            onClick={() => { setMode('signup'); setErrorMsg(''); }}
          >
            Create Account
          </button>
        </div>

        {/* Error Notification */}
        {errorMsg && (
          <div className="auth-error-banner" role="alert">
            <span className="auth-error-icon">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form-body">
          <div className="auth-field-group">
            <label htmlFor="auth-username" className="auth-field-label">
              Username
            </label>
            <input
              id="auth-username"
              type="text"
              className="auth-input-control"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. aryan_cs"
              autoComplete="username"
              required
              disabled={loading}
              maxLength={30}
            />
          </div>

          <div className="auth-field-group">
            <div className="auth-label-row">
              <label htmlFor="auth-password" className="auth-field-label">
                Password
              </label>
              <button
                type="button"
                className="auth-toggle-pwd-btn"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              id="auth-password"
              type={showPassword ? 'text' : 'password'}
              className="auth-input-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 10 characters"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              disabled={loading}
              minLength={10}
            />
          </div>

          <div className="auth-checkbox-row">
            <label className="auth-checkbox-label">
              <input
                id="auth-remember-me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={loading}
              />
              <span>Remember me for 30 days</span>
            </label>
          </div>

          {/* DPDP Act Privacy Notice for Sign-up */}
          {mode === 'signup' && (
            <div className="auth-dpdp-notice-box">
              <div className="dpdp-header">
                <span className="dpdp-pill">DPDP Act Privacy Notice</span>
              </div>
              <p className="dpdp-text">
                BitBytes stores only your chosen username, a cryptographically salted scrypt password hash, and reading timestamps to sync your reading streak across devices. We never sell, track, or share your data.
              </p>
              <label className="auth-checkbox-label dpdp-consent-row">
                <input
                  id="auth-dpdp-consent"
                  type="checkbox"
                  checked={dpdpConsent}
                  onChange={(e) => setDpdpConsent(e.target.checked)}
                  required
                  disabled={loading}
                />
                <span className="dpdp-consent-text">
                  I consent to the storage of my username, password hash, and reading progress.
                </span>
              </label>
            </div>
          )}

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Log In →' : 'Create Account & Start Reading →'}
          </button>
        </form>

        {/* Operator Link */}
        <div className="auth-footer-help">
          <button
            type="button"
            className="auth-operator-link"
            onClick={onGoToOperator}
          >
            Are you a pipeline maintainer? Access Operator Console →
          </button>
        </div>
      </div>
    </div>
  );
}
