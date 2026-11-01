import { useState } from 'react';

export default function NoteDetailView({ post, onBack }) {
  const [copiedCode, setCopiedCode] = useState(false);

  if (!post) {
    return (
      <article className="detail-view-card">
        <div className="detail-nav-bar">
          <button type="button" className="btn-back-feed" onClick={onBack}>
            ← Back to all dispatches
          </button>
        </div>
        <p className="detail-summary-p">Note not found in recent dispatches.</p>
      </article>
    );
  }

  function handleCopyCode() {
    if (post.code_snippet) {
      navigator.clipboard.writeText(post.code_snippet);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  }

  const dateStr = post.date ? post.date.slice(0, 10) : '';
  const timeStr = post.date && post.date.length >= 16 ? `${post.date.slice(11, 16)} UTC` : '';

  return (
    <article className="detail-view-card">
      {/* Navigation & Breadcrumbs */}
      <div className="detail-nav-bar">
        <button type="button" className="btn-back-feed" onClick={onBack}>
          ← Back to all dispatches
        </button>
        {post.read_minutes ? (
          <span className="dominant-timestamp">{post.read_minutes} min read</span>
        ) : null}
      </div>

      {/* Top Meta */}
      <div className="detail-top-meta">
        <span className="dominant-badge">{post.track || 'Engineering Note'}</span>
        {dateStr && <span>{dateStr}</span>}
        {timeStr && <span>• {timeStr}</span>}
        {post.source_count >= 2 && (
          <span>• Verified across {post.source_count} sources</span>
        )}
      </div>

      {/* Title & Subtitle */}
      <div>
        <h1 className="detail-title">{post.title}</h1>
        {post.subtitle && <p className="detail-subtitle">{post.subtitle}</p>}
      </div>

      {/* Provenance: Source or References */}
      {post.source && post.source.url ? (
        <div className="dominant-source-strip">
          <span className="source-label">Source article:</span>
          <a
            href={post.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="dominant-source-title"
          >
            {post.source.title || post.source.url} ↗
          </a>
          {post.source.domain && (
            <a
              href={post.source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="source-domain-chip"
            >
              {post.source.domain}
            </a>
          )}
          {post.source_count >= 2 && (
            <span className="verified-count-label">
              Verified across {post.source_count} sources
            </span>
          )}
        </div>
      ) : post.references && post.references.length > 0 ? (
        <div className="dominant-source-strip">
          <span className="source-label">Canonical references:</span>
          {post.references.map((ref, idx) => (
            <a
              key={idx}
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="dominant-source-title"
            >
              {ref.title} ↗
            </a>
          ))}
        </div>
      ) : null}

      {/* Hook / Summary */}
      {post.summary && (
        <div>
          <h2 className="detail-section-title">Context & Core Mechanism</h2>
          <p className="detail-summary-p">{post.summary}</p>
        </div>
      )}

      {/* Key Architectural Points */}
      {post.key_points && post.key_points.length > 0 && (
        <div>
          <h2 className="detail-section-title">Engineering Invariants</h2>
          <ul className="detail-points-list">
            {post.key_points.map((pt, idx) => (
              <li key={idx}>{pt}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Code Snippet with Copy Button */}
      {post.code_snippet && (
        <div>
          <div className="code-container">
            <div className="code-header-bar">
              <span>Code Snippet / Implementation Invariant</span>
              <button
                type="button"
                className="btn-copy-code"
                onClick={handleCopyCode}
              >
                {copiedCode ? 'Copied to clipboard' : 'Copy code'}
              </button>
            </div>
            <pre className="code-pre-block">
              <code>{post.code_snippet}</code>
            </pre>
          </div>
        </div>
      )}

      {/* Complexity & Interview Tip */}
      {(post.complexity || post.interview_tip) && (
        <div className="detail-meta-box">
          {post.complexity && (
            <div>
              <strong>Systems Trade-off:</strong>{' '}
              <span>
                {post.complexity.time_or_memory}
                {post.complexity.paradigm ? ` (${post.complexity.paradigm})` : ''}
              </span>
            </div>
          )}
          {post.interview_tip && (
            <div>
              <strong>Staff / Systems Interview Tip:</strong>{' '}
              <span>{post.interview_tip}</span>
            </div>
          )}
        </div>
      )}

      {/* Actions Strip */}
      <div className="dominant-actions-strip">
        <a
          href={post.telegram_url || 'https://t.me/csbites'}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-read-channel"
        >
          Read note in Telegram (@csbites) →
        </a>

        {post.archive_url && (
          <a
            href={post.archive_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-full-note"
          >
            Git Markdown archive ↗
          </a>
        )}
      </div>
    </article>
  );
}
