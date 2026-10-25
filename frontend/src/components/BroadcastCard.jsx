import { useEffect, useState } from 'react';
import { getNextBroadcast, triggerBroadcast } from '../services/api.js';

export default function BroadcastCard({ onBroadcastComplete }) {
  const [nextPost, setNextPost] = useState(null);
  const [loadingNext, setLoadingNext] = useState(true);
  const [broadcasting, setBroadcasting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  async function fetchNext() {
    try {
      setLoadingNext(true);
      const res = await getNextBroadcast();
      if (res && res.next) {
        setNextPost(res.next);
      }
    } catch (err) {
      console.warn('Could not fetch next broadcast post:', err);
    } finally {
      setLoadingNext(false);
    }
  }

  useEffect(() => {
    fetchNext();
  }, []);

  async function handleBroadcast() {
    setBroadcasting(true);
    setError('');
    setResult(null);

    try {
      const res = await triggerBroadcast();
      if (res && res.success) {
        setResult(res);
        // Refresh the next post in the rotation
        fetchNext();
        if (typeof onBroadcastComplete === 'function') {
          onBroadcastComplete(res);
        }
      } else {
        setError(res?.error || 'Broadcast failed.');
      }
    } catch (err) {
      setError(err.message || 'Error triggering broadcast.');
    } finally {
      setBroadcasting(false);
    }
  }

  return (
    <section className="panel broadcast-panel">
      <div className="broadcast-header">
        <div>
          <h2>Telegram Channel Broadcast</h2>
          <small>Automated B.Tech CS Bites Delivery Pipeline</small>
        </div>
        <a
          href="https://t.me/csbites"
          target="_blank"
          rel="noopener noreferrer"
          className="channel-pill"
          title="Open live Telegram Channel"
        >
          @csbites [Open Channel]
        </a>
      </div>

      <div className="broadcast-body">
        {loadingNext ? (
          <div className="loading" style={{ margin: '14px 0' }}>
            <span className="spinner" /> Fetching queued concept...
          </div>
        ) : nextPost ? (
          <div className="next-concept-card">
            <div className="concept-meta">
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="badge-track">{nextPost.track || 'CS Concept'}</span>
                {nextPost.radar_enabled && <span className="badge-radar">Live AI Radar</span>}
              </div>
              <span className="concept-id">Queue ID: {nextPost.id}</span>
            </div>
            <h3 className="concept-title">{nextPost.title}</h3>
            {nextPost.subtitle && <p className="concept-subtitle">{nextPost.subtitle}</p>}
            {nextPost.summary && <p className="concept-summary">{nextPost.summary}</p>}

            {nextPost.tags && nextPost.tags.length > 0 && (
              <div className="concept-tags">
                {nextPost.tags.map((tag) => (
                  <span key={tag} className="tag-chip">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="empty">No queued posts found.</p>
        )}

        {error && (
          <div className="alert" role="alert" style={{ marginTop: '14px' }}>
            {error}
          </div>
        )}

        {result && (
          <div className="broadcast-success" style={{ marginTop: '14px' }}>
            <div className="success-header">
              <span>Broadcast Successfully Sent</span>
            </div>
            <p className="success-topic">
              <strong>Delivered:</strong> {result.post?.title}
            </p>
            <div className="success-details">
              {result.post?.curation_engine && (
                <div>
                  • Engine: <code>{result.post.curation_engine}</code>
                </div>
              )}
              {result.post?.source_headline && (
                <div>
                  • News Hook: <i>{result.post.source_headline}</i>
                </div>
              )}
              {result.post?.source_url && (
                <div>
                  • Source URL:{' '}
                  <a
                    href={result.post.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {result.post.source_url}
                  </a>
                </div>
              )}
              {result.telegram?.message_id && (
                <div>
                  • Telegram Message ID:{' '}
                  <a
                    href={`https://t.me/csbites/${result.telegram.message_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    #{result.telegram.message_id} (View in Telegram)
                  </a>
                </div>
              )}
              {result.bridge?.bridgeId && (
                <div>
                  • Cosmitude Bridge ID: <code>{result.bridge.bridgeId}</code>
                </div>
              )}
              {result.git?.relative_path && (
                <div>
                  • Archived to: <code>{result.git.relative_path}</code>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="actions" style={{ marginTop: '16px' }}>
          <button
            type="button"
            className="primary broadcast-btn"
            onClick={handleBroadcast}
            disabled={broadcasting}
          >
            {broadcasting ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                <span>Broadcasting to @csbites...</span>
              </>
            ) : (
              <span>Broadcast Now</span>
            )}
          </button>
          <button
            type="button"
            className="secondary-btn"
            onClick={fetchNext}
            disabled={broadcasting}
          >
            Refresh Queue
          </button>
        </div>
      </div>
    </section>
  );
}
