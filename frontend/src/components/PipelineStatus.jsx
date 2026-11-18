import { useState, useEffect } from 'react';

const TONE = { online: 'ok', connected: 'ok', offline: 'bad', disconnected: 'bad' };
const LABEL = {
  online: 'Online', connected: 'Connected', offline: 'Offline',
  disconnected: 'Disconnected', unconfigured: 'Not configured', unknown: 'Unknown',
};

export default function PipelineStatus({ health }) {
  const [pipelineStatus, setPipelineStatus] = useState(null);

  useEffect(() => {
    fetch('/status.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setPipelineStatus(data))
      .catch(() => {});
  }, []);

  const nodes = [
    { name: 'Frontend', state: 'online' },
    { name: 'Middleware', state: health ? 'online' : 'offline' },
    { name: 'Cosmitude Agent', state: health?.agent?.state ?? 'unknown' },
    { name: 'Cosmitude Bridge', state: health?.bridge?.state ?? 'unknown' },
  ];

  return (
    <div className="pipeline-container">
      <ol className="pipeline" aria-label="Connection status">
        {nodes.map((n) => (
          <li key={n.name} className={`node ${TONE[n.state] || 'idle'}`}>
            <span className="dot" aria-hidden="true" />
            <span className="node-name">{n.name}</span>
            <span className="node-state">{LABEL[n.state] || n.state}</span>
          </li>
        ))}
      </ol>

      {pipelineStatus && (
        <div className="pipeline-automation-status" style={{
          marginTop: '10px',
          padding: '8px 12px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '4px',
          fontSize: '12px',
          fontFamily: 'var(--font-mono, monospace)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center'
        }}>
          <div>
            <span style={{ opacity: 0.6 }}>Last Pipeline Run: </span>
            <strong>{pipelineStatus.last_run ? new Date(pipelineStatus.last_run).toLocaleDateString() + ' ' + new Date(pipelineStatus.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}</strong>
          </div>
          <div>
            <span style={{ opacity: 0.6 }}>Outcome: </span>
            <span style={{
              color: pipelineStatus.outcome?.includes('publish') ? '#10B981' : pipelineStatus.outcome === 'skipped' ? '#F59E0B' : '#EF4444',
              fontWeight: 600
            }}>
              {pipelineStatus.outcome?.toUpperCase() || 'IDLE'}
            </span>
          </div>
          {pipelineStatus.last_post_title && (
            <div style={{ maxWidth: '350px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <span style={{ opacity: 0.6 }}>Post: </span>
              <span>{pipelineStatus.last_post_title}</span>
            </div>
          )}
          {pipelineStatus.last_error && (
            <div style={{ color: '#EF4444' }}>
              <span>Error: {pipelineStatus.last_error}</span>
            </div>
          )}
          {pipelineStatus.last_skip_reason && (
            <div style={{ color: '#F59E0B' }}>
              <span>Skip: {pipelineStatus.last_skip_reason}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
