import { useCallback, useEffect, useState } from 'react';
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

  const refreshHealth = useCallback(() => getHealth().then(setHealth).catch(() => setHealth(null)), []);
  const refreshHistory = useCallback(() => getRequests().then((d) => setHistory(d.requests)).catch(() => {}), []);
  const handleBroadcastComplete = useCallback(() => setHistoryRefreshKey((k) => k + 1), []);

  useEffect(() => {
    getTypes().then((d) => setTypes(d.types)).catch((e) => setTypesError(e.message));
    refreshHealth();
    refreshHistory();
    const timer = setInterval(refreshHealth, 10000);
    return () => clearInterval(timer);
  }, [refreshHealth, refreshHistory]);

  const hasPending = history.some((r) => r.status === 'pending');
  useEffect(() => {
    if (!hasPending) return undefined;
    const timer = setInterval(refreshHistory, 2500);
    return () => clearInterval(timer);
  }, [hasPending, refreshHistory]);

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
      await refreshHistory();
      refreshHealth();
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
            <ResponsePanel request={history.find((r) => r.id === selectedId)} />
            <HistoryList requests={history} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
        </div>
      </details>
    </div>
  );
}
