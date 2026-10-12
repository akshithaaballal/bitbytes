import { useState } from 'react';

export default function RequestForm({ types, submitting, error, onSubmit }) {
  const [type, setType] = useState('');
  const [message, setMessage] = useState('');
  const activeType = type || types[0]?.id || '';
  const hint = types.find((t) => t.id === activeType)?.hint;
  const canSend = !submitting && activeType && message.trim();

  async function send() {
    if (!canSend) return;
    const ok = await onSubmit({ type: activeType, message });
    if (ok) setMessage('');
  }

  return (
    <section className="panel">
      <h2>New request</h2>
      <label className="field">
        <span>Request type</span>
        <select value={activeType} onChange={(e) => setType(e.target.value)} disabled={submitting}>
          {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        {hint && <small>{hint}</small>}
      </label>
      <label className="field">
        <span>Message</span>
        <textarea
          rows={5}
          value={message}
          maxLength={2000}
          placeholder="Describe what you need from the agent"
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) send(); }}
          disabled={submitting}
        />
      </label>
      {error && <p className="alert" role="alert">{error}</p>}
      <div className="actions">
        <button className="primary" onClick={send} disabled={!canSend}>
          {submitting ? 'Sending…' : 'Send request'}
        </button>
        <small>Ctrl or Cmd + Enter also sends</small>
      </div>
    </section>
  );
}
