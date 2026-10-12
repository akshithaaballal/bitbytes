import { useCallback, useEffect, useState } from 'react';
import PipelineStatus from '../components/PipelineStatus.jsx';
import BroadcastCard from '../components/BroadcastCard.jsx';
import BroadcastHistory from '../components/BroadcastHistory.jsx';
import { getHealth } from '../services/api.js';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const refreshHealth = useCallback(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    refreshHealth();
    const timer = setInterval(refreshHealth, 10000);
    return () => clearInterval(timer);
  }, [refreshHealth]);

  return (
    <div className="dashboard-layout">
      <PipelineStatus health={health} />
      <BroadcastCard onBroadcastComplete={() => setHistoryRefreshKey((k) => k + 1)} />
      <BroadcastHistory refreshKey={historyRefreshKey} />
    </div>
  );
}
