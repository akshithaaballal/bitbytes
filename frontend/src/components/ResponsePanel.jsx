const STATUS = { pending: 'Waiting for reply', completed: 'Completed', failed: 'Failed' };

export default function ResponsePanel({ request }) {
  if (!request) {
    return (
      <section className="panel">
        <h2>Response</h2>
        <p className="empty">Send a request or pick one from the history to see its response here.</p>
      </section>
    );
  }
  const output = typeof request.output === 'string' ? request.output : JSON.stringify(request.output, null, 2);
  return (
    <section className="panel" aria-live="polite">
      <h2>Response</h2>
      <div className="meta">
        <span className={`badge ${request.status}`}>{STATUS[request.status]}</span>
        <span>{request.type}</span>
        <span>{new Date(request.createdAt).toLocaleTimeString()}</span>
      </div>
      <p className="sent">{request.message}</p>
      {request.status === 'pending' && (
        <p className="loading"><span className="spinner" aria-hidden="true" />Cosmitude Bridge replies can take several seconds.</p>
      )}
      {request.status === 'completed' && <pre className="output">{output || 'The agent returned an empty reply.'}</pre>}
      {request.status === 'failed' && <p className="alert">{request.error}</p>}
    </section>
  );
}
