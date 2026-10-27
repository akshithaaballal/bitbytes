import { useEffect, useState, useRef } from 'react';
import { getBroadcastHistory, triggerBroadcast, getBroadcastStatus } from '../services/api.js';
import { TELEGRAM_URL } from '../constants.js';

export default function BroadcastCard({ onBroadcastComplete }) {
  const [lastRun, setLastRun] = useState(null);
  const [loadingLast, setLoadingLast] = useState(true);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isDryRun, setIsDryRun] = useState(true);

  // Job tracking state
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobStage, setJobStage] = useState(null);
  const [jobResult, setJobResult] = useState(null);
  const [jobError, setJobError] = useState('');
  const pollTimerRef = useRef(null);

  // Keep onBroadcastComplete in a ref so polling effect doesn't restart on parent re-renders
  const onBroadcastCompleteRef = useRef(onBroadcastComplete);
  onBroadcastCompleteRef.current = onBroadcastComplete;

  const confirmBtnRef = useRef(null);

  // Handle modal escape key and focus
  useEffect(() => {
    if (!showConfirmModal) return;

    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setShowConfirmModal(false);
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    const focusTimer = setTimeout(() => {
      confirmBtnRef.current?.focus();
    }, 50);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(focusTimer);
    };
  }, [showConfirmModal]);

  async function fetchLastRun() {
    try {
      setLoadingLast(true);
      const res = await getBroadcastHistory();
      if (res && Array.isArray(res.history) && res.history.length > 0) {
        setLastRun(res.history[0]);
      }
    } catch (err) {
      console.warn('Could not fetch last broadcast run:', err);
    } finally {
      setLoadingLast(false);
    }
  }

  useEffect(() => {
    fetchLastRun();
  }, []);

  // Poll active broadcast job without tearing down on onBroadcastComplete change
  useEffect(() => {
    if (!activeJobId) return;

    async function poll() {
      try {
        const res = await getBroadcastStatus(activeJobId);
        if (res && res.stage) {
          setJobStage(res.stage);
          if (res.stage === 'done' || res.stage === 'skipped') {
            setJobResult(res.result);
            setActiveJobId(null);
            fetchLastRun();
            if (typeof onBroadcastCompleteRef.current === 'function') {
              onBroadcastCompleteRef.current(res.result);
            }
          } else if (res.stage === 'failed') {
            setJobError(res.error || 'Broadcast execution failed');
            setActiveJobId(null);
            fetchLastRun();
          }
        }
      } catch (err) {
        setJobError(err.message || 'Status check failed');
        setActiveJobId(null);
      }
    }

    pollTimerRef.current = setInterval(poll, 1500);
    return () => clearInterval(pollTimerRef.current);
  }, [activeJobId]);

  async function handleStartBroadcast() {
    setShowConfirmModal(false);
    setJobError('');
    setJobResult(null);
    setJobStage('starting');

    try {
      const res = await triggerBroadcast({ dry_run: isDryRun });
      if (res && res.jobId) {
        setActiveJobId(res.jobId);
        setJobStage(res.status || 'crawling');
      } else {
        setJobError('Failed to initialize broadcast job.');
      }
    } catch (err) {
      if (err.status === 409) {
        setJobError('A broadcast job is already running. Please wait for it to complete.');
      } else {
        setJobError(err.message || 'Error triggering broadcast.');
      }
    }
  }

  return (
    <section className="panel broadcast-panel">
      <div className="broadcast-header">
        <div>
          <h2>Broadcast Dispatch Pipeline</h2>
          <small>Automated B.Tech CS Bites Delivery Pipeline (Twice Daily: 03:00 & 15:00 UTC)</small>
        </div>
        <a
          href={TELEGRAM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="channel-pill"
          title="Open live Telegram Channel"
        >
          @csbites [Open Channel]
        </a>
      </div>

      <div className="broadcast-body">
        {/* Last Run Summary (Replaces static Live AI Radar card) */}
        {loadingLast ? (
          <div className="skeleton-dominant">Loading last execution telemetry...</div>
        ) : lastRun ? (
          <div className="next-concept-card">
            <div className="concept-meta">
              <span className="dominant-badge">Last Run Summary</span>
              <span className="dominant-timestamp">
                {lastRun.timestamp ? lastRun.timestamp.slice(0, 19).replace('T', ' ') + ' UTC' : '-'}
              </span>
            </div>

            <h3 className="concept-title">
              {lastRun.title || (lastRun.skipped_reason ? 'Pipeline Run Skipped' : 'Automated Dispatch')}
            </h3>

            <div className="detail-meta-box">
              <div>
                <strong>Engine:</strong> <code>{lastRun.engine || lastRun.source || 'automated'}</code>
              </div>
              {lastRun.source_headline && (
                <div>
                  <strong>Source Lead:</strong> <span>{lastRun.source_headline}</span>
                </div>
              )}
              {lastRun.fallback_used && (
                <div>
                  <strong>Fallback Note:</strong> <span>Triggered evergreen content bank rotation</span>
                </div>
              )}
              {lastRun.skipped_reason && (
                <div>
                  <strong>Skipped Reason:</strong> <span>{lastRun.skipped_reason}</span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <p className="empty">No broadcast runs logged yet.</p>
        )}

        {/* Polling / Stage Indicator */}
        {activeJobId && (
          <div className="stage-tracker-box">
            <span className="spinner" />
            <span>Active Job ({activeJobId.slice(0, 8)}): Stage: <strong>{jobStage}</strong>...</span>
          </div>
        )}

        {/* Error notification */}
        {jobError && (
          <div className="alert" role="alert">
            {jobError}
          </div>
        )}

        {/* Success / Result notification */}
        {jobResult && (
          <div className="broadcast-success">
            <div className="success-header">
              <span>Broadcast Pipeline Execution Complete</span>
            </div>
            {jobResult.skipped ? (
              <p>Run completed without publish: <i>{jobResult.skipped_reason}</i></p>
            ) : (
              <div className="success-details">
                <div>Topic: <strong>{jobResult.post?.title}</strong></div>
                {jobResult.telegram?.telegram_url && (
                  <div>
                    Telegram:{' '}
                    <a href={jobResult.telegram.telegram_url} target="_blank" rel="noopener noreferrer">
                      View message ↗
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="actions">
          <button
            type="button"
            className="primary broadcast-btn"
            onClick={() => setShowConfirmModal(true)}
            disabled={!!activeJobId}
          >
            {activeJobId ? 'Broadcasting...' : 'Broadcast Now'}
          </button>
          <button
            type="button"
            className="secondary-btn"
            onClick={fetchLastRun}
            disabled={!!activeJobId}
          >
            Refresh Summary
          </button>
        </div>
      </div>

      {/* Confirm Dialog Modal */}
      {showConfirmModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="modal-dialog">
            <h3 id="modal-title">Confirm Broadcast Dispatch</h3>
            <p>
              This triggers the autonomous content pipeline to crawl verified sources, curate a grounded CS note, and optionally broadcast across channels.
            </p>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isDryRun}
                onChange={(e) => setIsDryRun(e.target.checked)}
              />
              <span>Dry run (simulate broadcast without posting to live Telegram or Git)</span>
            </label>

            <div className="modal-actions">
              <button
                type="button"
                className="btn-login-cancel"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </button>
              <button
                ref={confirmBtnRef}
                type="button"
                className="btn-login-submit"
                onClick={handleStartBroadcast}
              >
                Confirm & Run
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
