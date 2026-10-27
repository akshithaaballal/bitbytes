import { useState } from 'react';
import { operatorLogin } from '../services/api.js';

export default function OperatorLogin({ onLoginSuccess, onCancel }) {
  const [passcode, setPasscode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await operatorLogin(passcode.trim());
      onLoginSuccess();
    } catch (err) {
      setError(err.message || 'Incorrect operator passcode.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="operator-login-overlay">
      <div className="operator-login-card">
        <div>
          <span className="hero-smallcaps-label">Restricted Area</span>
          <h2 className="operator-login-title">Operator Gateway</h2>
          <p className="operator-login-sub">
            Internal controls for manual broadcasts and pipeline telemetry.
          </p>
        </div>

        <form onSubmit={handleLogin}>
          <label htmlFor="passcode-input" className="login-field-label">
            Operator Passcode
          </label>
          <input
            id="passcode-input"
            type="password"
            className="login-input"
            placeholder="Enter passcode..."
            value={passcode}
            onChange={(e) => setPasscode(e.target.value)}
            autoFocus
            required
          />

          {error && <div className="login-error-msg">{error}</div>}

          <div className="login-btn-row">
            <button
              type="submit"
              className="btn-login-submit"
              disabled={loading || !passcode}
            >
              {loading ? 'Authenticating...' : 'Unlock Console →'}
            </button>

            <button
              type="button"
              className="btn-login-cancel"
              onClick={onCancel}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
