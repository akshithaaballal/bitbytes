import { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import PipelineStatus from '../components/PipelineStatus.jsx';
import BroadcastCard from '../components/BroadcastCard.jsx';
import RequestForm from '../components/RequestForm.jsx';
import ResponsePanel from '../components/ResponsePanel.jsx';
import HistoryList from '../components/HistoryList.jsx';
import BroadcastHistory from '../components/BroadcastHistory.jsx';
import { getHealth, getTypes, getRequests, sendRequest } from '../services/api.js';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [types, setTypes] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [typesError, setTypesError] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  // Abort controllers to cancel stale in-flight fetches
  const healthAbortRef = useRef(null);
  const historyAbortRef = useRef(null);
  const pendingPollRef = useRef(null);

  const handleBroadcastComplete = useCallback(() => setHistoryRefreshKey((k) => k + 1), []);

  // --- Abortable health poll (every 30 s) ---
  const fetchHealth = useCallback(() => {
    if (healthAbortRef.current) healthAbortRef.current.abort();
    const ac = new AbortController();
    healthAbortRef.current = ac;
    getHealth({ signal: ac.signal })
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => { healthAbortRef.current = null; });
  }, []);

  // --- Abortable history fetch (deduplicates overlapping calls) ---
  const fetchHistory = useCallback(() => {
    if (historyAbortRef.current) return; // skip if one is already in flight
    const ac = new AbortController();
    historyAbortRef.current = ac;
    getRequests({ signal: ac.signal })
      .then((d) => setHistory(d.requests))
      .catch(() => {})
      .finally(() => { historyAbortRef.current = null; });
  }, []);

  // --- Initial load + 30 s health timer ---
  useEffect(() => {
    getTypes().then((d) => setTypes(d.types)).catch((e) => setTypesError(e.message));
    fetchHealth();
    fetchHistory();
    const healthTimer = setInterval(fetchHealth, 30_000);
    const historyTimer = setInterval(fetchHistory, 15_000);
    return () => {
      clearInterval(healthTimer);
      clearInterval(historyTimer);
      if (healthAbortRef.current) healthAbortRef.current.abort();
      if (historyAbortRef.current) historyAbortRef.current.abort();
    };
  }, [fetchHealth, fetchHistory]);

  // --- Pending-request back-off poll (5 s → 10 s → 20 s → 30 s cap) ---
  const hasPending = useMemo(() => history.some((r) => r.status === 'pending'), [history]);
  useEffect(() => {
    if (!hasPending) return undefined;
    let delay = 5000;
    const tick = () => {
      fetchHistory();
      delay = Math.min(delay * 2, 30_000);
      pendingPollRef.current = setTimeout(tick, delay);
    };
    pendingPollRef.current = setTimeout(tick, delay);
    return () => clearTimeout(pendingPollRef.current);
  }, [hasPending, fetchHistory]);

  // Memoize selected request to avoid repeated .find() on every render
  const selectedRequest = useMemo(
    () => history.find((r) => r.id === selectedId),
    [history, selectedId],
  );

  async function handleSubmit(payload) {
    setSubmitting(true);
    setSubmitError('');
    try {
      const { request } = await sendRequest(payload);
      setSelectedId(request.id);
      return true;
    } catch (e) {
      setSubmitError(e.message);
      return false;
    } finally {
      fetchHistory();
      fetchHealth();
      setSubmitting(false);
    }
  }

  return (
    <div className="dashboard-layout">
      <PipelineStatus health={health} />
      <BroadcastCard onBroadcastComplete={handleBroadcastComplete} />

      {/* Audit Log Table */}
      <BroadcastHistory refreshKey={historyRefreshKey} />

      {/* Advanced Cosmitude Bridge Section Collapsed */}
      <details className="collapsible-wrapper">
        <summary className="collapsible-summary">Advanced: Cosmitude bridge</summary>
        <div className="collapsible-content">
          <div className="grid">
            <RequestForm types={types} submitting={submitting} error={submitError || typesError} onSubmit={handleSubmit} />
            <ResponsePanel request={selectedRequest} />
            <HistoryList requests={history} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        </div>
      </details>
    </div>
  );
}
