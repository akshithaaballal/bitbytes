import { useEffect, useState } from 'react';
import { getBroadcastHistory } from '../services/api.js';

export default function BroadcastHistory({ refreshKey }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadHistory() {
    try {
      setLoading(true);
      const res = await getBroadcastHistory();
      if (res && res.history) {
        setHistory(res.history);
      }
    } catch (err) {
      console.warn('Could not fetch broadcast history:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, [refreshKey]);

  return (
    <section className="panel broadcast-history-panel">
      <div className="history-header">
        <div>
          <h2>Broadcast Audit Log</h2>
          <small>Verified delivery log across Telegram channel and Git archive</small>
        </div>
        <button type="button" className="secondary-btn" onClick={loadHistory} disabled={loading}>
          Refresh Log
        </button>
      </div>

      {loading && history.length === 0 ? (
        <div className="loading" style={{ margin: '14px 0' }}>
          <span className="spinner" /> Loading audit history...
        </div>
      ) : history.length === 0 ? (
        <p className="empty">No broadcasts recorded yet.</p>
      ) : (
        <div className="history-table-container">
          <table className="broadcast-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Track</th>
                <th>Concept Title</th>
                <th>Telegram</th>
                <th>Git Archive</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, idx) => (
                <tr key={item.timestamp || idx}>
                  <td className="cell-time">
                    {item.timestamp ? new Date(item.timestamp).toLocaleString([], {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    }) : '-'}
                  </td>
                  <td>
                    <span className="badge-track">{item.track || 'CS Concept'}</span>
                  </td>
                  <td className="cell-title">
                    <strong>{item.title}</strong>
                    <span className="post-id-tag">({item.post_id})</span>
                  </td>
                  <td>
                    <span className={`badge ${item.telegram ? 'completed' : 'failed'}`}>
                      {item.telegram ? 'Delivered' : 'Pending'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${item.git ? 'completed' : 'failed'}`}>
                      {item.git ? 'Archived' : 'Pending'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
