import { useEffect, useState } from 'react';
import { getBroadcastHistory } from '../services/api.js';

const PAGE_SIZE = 20;

export default function BroadcastHistory({ refreshKey }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  async function loadHistory() {
    try {
      setLoading(true);
      const res = await getBroadcastHistory();
      if (res && res.history) {
        setHistory(res.history);
        setCurrentPage(1);
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

  const totalPages = Math.max(1, Math.ceil(history.length / PAGE_SIZE));
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const pageItems = history.slice(startIndex, startIndex + PAGE_SIZE);

  function formatTime(isoStr) {
    if (!isoStr) return '-';
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr.slice(0, 16);
    }
  }

  return (
    <section className="panel broadcast-history-panel">
      <div className="history-header">
        <div>
          <h2>Broadcast Audit Log</h2>
          <small>Verified delivery log across Telegram channel, Git archive, and Instagram</small>
        </div>
        <button type="button" className="secondary-btn" onClick={loadHistory} disabled={loading}>
          Refresh Log
        </button>
      </div>

      {loading && history.length === 0 ? (
        <div className="skeleton-dominant">Loading audit history...</div>
      ) : history.length === 0 ? (
        <p className="empty">No broadcasts recorded yet.</p>
      ) : (
        <>
          <div className="history-table-container">
            <table className="broadcast-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Track</th>
                  <th>Concept Title</th>
                  <th>Source</th>
                  <th>Telegram</th>
                  <th>Instagram</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((item) => {
                  const itemKey = `${item.post_id || 'skipped'}_${item.timestamp}`;
                  const isSkipped = !!item.skipped_reason;
                  const tgDelivered = !!item.telegram;
                  const igDelivered = !!item.instagram;

                  return (
                    <tr key={itemKey}>
                      <td className="cell-time">{formatTime(item.timestamp)}</td>
                      <td>
                        <span className="badge-track">{item.track || 'CS Concept'}</span>
                      </td>
                      <td className="cell-title">
                        <strong>{item.title || (isSkipped ? `[Skipped] ${item.skipped_reason}` : 'Broadcast Run')}</strong>
                        {item.post_id && <span className="post-id-tag">({item.post_id})</span>}
                      </td>
                      <td>
                        {item.source_url ? (
                          <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-headline-link"
                          >
                            {item.source_headline || item.source_url} ↗
                          </a>
                        ) : (
                          <span>{item.source_headline || item.source || '-'}</span>
                        )}
                      </td>
                      <td>
                        {tgDelivered ? (
                          <a
                            href="https://t.me/csbites"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="badge completed"
                          >
                            Delivered ↗
                          </a>
                        ) : isSkipped ? (
                          <span className="badge skipped">Skipped</span>
                        ) : (
                          <span className="badge failed">Failed</span>
                        )}
                      </td>
                      <td>
                        <span className={`badge ${igDelivered ? 'completed' : 'skipped'}`}>
                          {igDelivered ? 'Published' : 'Skipped'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="ledger-load-more">
              <button
                type="button"
                className="btn-load-compact"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>
              <span className="col-date">
                Page {currentPage} of {totalPages} ({history.length} dispatches)
              </span>
              <button
                type="button"
                className="btn-load-compact"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
