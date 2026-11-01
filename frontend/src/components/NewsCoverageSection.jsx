import { useState, useEffect } from 'react';

export default function NewsCoverageSection({ searchInputRef, onSelectPost }) {
  const [feed, setFeed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedTrack, setSelectedTrack] = useState('ALL');
  const [limit, setLimit] = useState(15);

  async function loadFeed() {
    setLoading(true);
    setError(false);
    try {
      const res = await fetch('/feed.json');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setFeed(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFeed();
  }, []);

  const posts = feed?.posts || [];

  // Derive dynamic filter tracks from current feed
  const availableTracks = [
    'ALL',
    ...Array.from(new Set(posts.map((p) => p.track).filter(Boolean))),
  ];

  // Filtering
  const filtered = posts.filter((item) => {
    const matchesTrack =
      selectedTrack === 'ALL' ||
      (item.track && item.track.toLowerCase() === selectedTrack.toLowerCase());

    const term = search.toLowerCase();
    const domain = item.source?.domain || '';
    const matchesSearch =
      search === '' ||
      (item.title && item.title.toLowerCase().includes(term)) ||
      (item.track && item.track.toLowerCase().includes(term)) ||
      (item.summary && item.summary.toLowerCase().includes(term)) ||
      domain.toLowerCase().includes(term);

    return matchesTrack && matchesSearch;
  });

  const dominantItem = filtered[0];
  const compactRows = filtered.slice(1, limit);

  function formatDate(isoStr) {
    if (!isoStr) return '';
    return isoStr.slice(0, 10);
  }

  function formatTime(isoStr) {
    if (!isoStr || isoStr.length < 16) return '';
    return `${isoStr.slice(11, 16)} UTC`;
  }

  function handleOpenNote(id) {
    window.location.hash = `#p/${id}`;
    if (typeof onSelectPost === 'function') {
      onSelectPost(id);
    }
  }

  return (
    <section className="ledger-section" id="coverage">
      {/* Header & Filter Controls */}
      <div className="ledger-controls-header">
        <div className="ledger-title-strip">
          <h2 className="ledger-main-title">Dispatch Ledger</h2>
          {feed?.total ? (
            <span className="ledger-count-indicator">
              {feed.total} technical notes logged
            </span>
          ) : null}
        </div>

        <div className="ledger-filter-row">
          <div className="search-box-wrapper">
            <input
              ref={searchInputRef}
              type="text"
              className="search-input-field"
              placeholder="Search topics, tracks, or source domains..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search dispatches"
            />
            <span className="search-slash-badge" aria-hidden="true">
              /
            </span>
          </div>

          <div className="track-filter-chips" role="group" aria-label="Filter by track">
            {availableTracks.map((t) => (
              <button
                key={t}
                type="button"
                className={`filter-chip ${selectedTrack === t ? 'active' : ''}`}
                onClick={() => setSelectedTrack(t)}
                aria-pressed={selectedTrack === t}
              >
                {t === 'ALL' ? `All (${posts.length})` : t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading Skeleton (Zero Layout Shift) */}
      {loading && (
        <div>
          <div className="skeleton-dominant" aria-label="Loading latest note">
            Loading latest dispatch...
          </div>
          <div className="skeleton-table" aria-label="Loading notes ledger">
            Loading technical dispatches...
          </div>
        </div>
      )}

      {/* Error State with Retry Button */}
      {!loading && error && (
        <div className="compact-ledger-table">
          <div className="ledger-empty-state">
            <p>Couldn't load the latest notes.</p>
            <button
              type="button"
              className="btn-load-compact"
              onClick={loadFeed}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Empty Filter State */}
      {!loading && !error && filtered.length === 0 && (
        <div className="compact-ledger-table">
          <div className="ledger-empty-state">
            No notes found matching "{search}".
          </div>
        </div>
      )}

      {/* Data Loaded */}
      {!loading && !error && filtered.length > 0 && (
        <>
          {/* Dominant Latest Card */}
          {dominantItem && (
            <article className="latest-dominant-card">
              <div className="dominant-top-meta">
                <span className="dominant-badge">Latest dispatch</span>
                {dominantItem.track && (
                  <span className="dominant-track">{dominantItem.track}</span>
                )}
                <span className="dominant-timestamp">
                  {formatDate(dominantItem.date)}
                  {formatTime(dominantItem.date) ? ` • ${formatTime(dominantItem.date)}` : ''}
                  {dominantItem.read_minutes ? ` • ${dominantItem.read_minutes} min read` : ''}
                </span>
              </div>

              <h3 className="dominant-title">{dominantItem.title}</h3>

              {/* Source Provenance */}
              {dominantItem.source && dominantItem.source.url ? (
                <div className="dominant-source-strip">
                  <span className="source-label">Source article:</span>
                  <a
                    href={dominantItem.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="dominant-source-title"
                  >
                    {dominantItem.source.title || dominantItem.source.url} ↗
                  </a>
                  {dominantItem.source.domain && (
                    <a
                      href={dominantItem.source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-domain-chip"
                    >
                      {dominantItem.source.domain}
                    </a>
                  )}
                  {dominantItem.source_count >= 2 && (
                    <span className="verified-count-label">
                      verified across {dominantItem.source_count} sources
                    </span>
                  )}
                </div>
              ) : dominantItem.references && dominantItem.references.length > 0 ? (
                <div className="dominant-source-strip">
                  <span className="source-label">Canonical reference:</span>
                  <a
                    href={dominantItem.references[0].url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="dominant-source-title"
                  >
                    {dominantItem.references[0].title} ↗
                  </a>
                </div>
              ) : null}

              {dominantItem.summary && (
                <p className="dominant-hook">{dominantItem.summary}</p>
              )}

              <div className="dominant-actions-strip">
                <a
                  href={dominantItem.telegram_url || 'https://t.me/csbites'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-read-channel"
                >
                  Read in Telegram (@csbites) →
                </a>

                <button
                  type="button"
                  className="btn-full-note"
                  onClick={() => handleOpenNote(dominantItem.id)}
                >
                  Full note →
                </button>
              </div>
            </article>
          )}

          {/* Compact Rows */}
          {compactRows.length > 0 && (
            <div className="compact-ledger-table">
              <div className="ledger-table-head">
                <span>Date</span>
                <span>Track</span>
                <span>Topic</span>
                <span className="col-link">Source / Link</span>
              </div>

              {compactRows.map((row) => {
                const sourceUrl = row.source?.url || row.references?.[0]?.url;
                const sourceDomain = row.source?.domain || (sourceUrl ? 'reference' : '');
                const tgLink = row.telegram_url || 'https://t.me/csbites';

                return (
                  <div key={row.id} className="ledger-row">
                    <span className="col-date">{formatDate(row.date)}</span>
                    <span className="col-track" title={row.track}>
                      {row.track}
                    </span>
                    <div className="col-topic">
                      <button
                        type="button"
                        className="topic-title-link"
                        onClick={() => handleOpenNote(row.id)}
                      >
                        {row.title}
                      </button>
                      {sourceDomain && sourceUrl && (
                        <a
                          href={sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-domain-chip"
                          title={row.source?.title || 'Source article'}
                        >
                          {sourceDomain} ↗
                        </a>
                      )}
                    </div>
                    <div className="col-link">
                      <a
                        href={tgLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="channel-out-link"
                      >
                        Telegram →
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Load More Button */}
          {filtered.length > limit && (
            <div className="ledger-load-more">
              <button
                type="button"
                className="btn-load-compact"
                onClick={() => setLimit((prev) => prev + 15)}
              >
                Show more notes ({filtered.length - limit} remaining)
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
