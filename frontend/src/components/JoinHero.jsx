import { useState } from 'react';

export const DISPATCH_CADENCE = 'Dispatched twice daily (03:00 & 15:00 UTC)';

export default function JoinHero() {
  const [copied, setCopied] = useState(false);
  const [qrMode, setQrMode] = useState('official'); // 'official' | 'standard'

  function copyInvite() {
    navigator.clipboard.writeText('https://t.me/csbites');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="hero-section">
      {/* Editorial Intro */}
      <div className="hero-editorial">
        <span className="hero-smallcaps-label">Notebook / {DISPATCH_CADENCE}</span>

        <h1 className="hero-headline">
          Daily technical concepts from production systems.
        </h1>

        <p className="hero-lead-text">
          We read engineering incident reports, research papers, and architecture teardowns across verified sources. When a concept appears across multiple independent sources, we distill the core mechanism into a concise technical note and publish it to Telegram.
        </p>

        <div className="hero-actions-row">
          <a
            href="https://t.me/csbites"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-hero-primary"
            title="Open Telegram channel (@csbites)"
          >
            <span>Join channel (@csbites)</span>
            <span aria-hidden="true">→</span>
          </a>

          <button
            type="button"
            className="btn-hero-secondary"
            onClick={copyInvite}
          >
            {copied ? 'Link copied (t.me/csbites)' : 'Copy invite link'}
          </button>
        </div>

        {/* Fallback Direct App Links */}
        <div className="direct-links-row">
          <span className="direct-label">Direct app link:</span>
          <a
            href="tg://resolve?domain=csbites"
            className="direct-link-pill"
            title="Launch native Telegram app directly"
          >
            Launch App (tg://) →
          </a>
          <span aria-hidden="true">•</span>
          <a
            href="https://telegram.me/csbites"
            target="_blank"
            rel="noopener noreferrer"
            className="direct-link-pill"
            title="Open unblocked Telegram web gateway"
          >
            telegram.me/csbites ↗
          </a>
        </div>

        {/* Human details line */}
        <div className="hero-meta-footer">
          <span className="meta-item">{DISPATCH_CADENCE}</span>
          <span className="meta-item">•</span>
          <span className="meta-item">Curated by Akshithaa</span>
          <span className="meta-item">•</span>
          <span className="meta-item">No sponsored posts</span>
        </div>
      </div>

      {/* Right Column: Scan Box with QR toggle */}
      <aside className="hero-scan-box" aria-label="QR Code to Join Telegram">
        <div className="scan-box-header">
          <span className="scan-box-label">Phone Scan</span>
          <div className="qr-mode-switch" role="group" aria-label="Select QR style">
            <button
              type="button"
              className={`qr-mode-btn ${qrMode === 'official' ? 'active' : ''}`}
              onClick={() => setQrMode('official')}
            >
              Official Card
            </button>
            <button
              type="button"
              className={`qr-mode-btn ${qrMode === 'standard' ? 'active' : ''}`}
              onClick={() => setQrMode('standard')}
            >
              Standard QR
            </button>
          </div>
        </div>

        <div className="qr-frame">
          {qrMode === 'official' ? (
            <img
              src="/telegram_qr_official.png"
              alt="Official Telegram Card for @csbites"
              className="hero-qr-official"
              width="220"
              height="280"
            />
          ) : (
            <img
              src="/telegram_qr.png"
              alt="High Contrast QR code for @csbites"
              className="hero-qr-svg"
              width="180"
              height="180"
            />
          )}
        </div>

        <p className="scan-box-caption">
          Scan with your phone camera or in Telegram (Settings → Devices → Link Desktop or Scan QR) to join @csbites.
        </p>

        <div className="direct-links-row">
          <a href="tg://resolve?domain=csbites" className="direct-link-pill">
            Open in App (tg://)
          </a>
          <span aria-hidden="true">•</span>
          <a
            href="https://telegram.me/csbites"
            target="_blank"
            rel="noopener noreferrer"
            className="direct-link-pill"
          >
            Web Gateway (telegram.me)
          </a>
        </div>
      </aside>
    </section>
  );
}
