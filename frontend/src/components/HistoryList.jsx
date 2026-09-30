export default function HistoryList({ requests, selectedId, onSelect }) {
  return (
    <section className="panel">
      <h2>History</h2>
      {requests.length === 0 ? (
        <p className="empty">No requests yet. Your sent requests will appear here.</p>
      ) : (
        <ul className="history">
          {requests.map((r) => (
            <li key={r.id}>
              <button className={r.id === selectedId ? 'item selected' : 'item'} onClick={() => onSelect(r.id)}>
                <span className={`dot ${r.status}`} aria-hidden="true" />
                <span className="item-text">{r.message}</span>
                <span className="item-time">{new Date(r.createdAt).toLocaleTimeString()}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
