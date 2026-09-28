const TONE = { online: 'ok', connected: 'ok', offline: 'bad', disconnected: 'bad' };
const LABEL = {
  online: 'Online', connected: 'Connected', offline: 'Offline',
  disconnected: 'Disconnected', unconfigured: 'Not configured', unknown: 'Unknown',
};

export default function PipelineStatus({ health }) {
  const nodes = [
    { name: 'Frontend', state: 'online' },
    { name: 'Middleware', state: health ? 'online' : 'offline' },
    { name: 'Cosmitude Agent', state: health?.agent?.state ?? 'unknown' },
    { name: 'Cosmitude Bridge', state: health?.bridge?.state ?? 'unknown' },
  ];
  return (
    <ol className="pipeline" aria-label="Connection status">
      {nodes.map((n) => (
        <li key={n.name} className={`node ${TONE[n.state] || 'idle'}`}>
          <span className="dot" aria-hidden="true" />
          <span className="node-name">{n.name}</span>
          <span className="node-state">{LABEL[n.state] || n.state}</span>
        </li>
      ))}
    </ol>
  );
}
