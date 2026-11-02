import { useState } from 'react';

export const DISPATCH_CADENCE = 'Dispatched twice daily (03:00 & 15:00 UTC)';

export default function JoinHero() {
  const [copied, setCopied] = useState(false);

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

          <a
            href="tg://resolve?domain=csbites"
            className="btn-hero-secondary"
            title="Launch desktop or mobile Telegram app directly"
          >
            Open in App (tg://)
          </a>

          <button
            type="button"
            className="btn-hero-secondary"
            onClick={copyInvite}
          >
            {copied ? 'Link copied (t.me/csbites)' : 'Copy invite link'}
          </button>
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

      {/* Right Column: Scan Box with Official Telegram QR Card */}
      <aside className="hero-scan-box" aria-label="QR Code to Join Telegram">
        <div className="scan-box-header">
          <span className="scan-box-label">Phone Scan</span>
          <span className="scan-box-label">@CSBITES</span>
        </div>

        <div className="qr-frame">
          <a
            href="https://t.me/csbites"
            target="_blank"
            rel="noopener noreferrer"
            title="Click to open @csbites channel"
          >
            <img
              src="/telegram_official_card.png"
              alt="Official Telegram Channel QR Code for @csbites"
              className="hero-qr-img"
              width="210"
              height="266"
            />
          </a>
        </div>

        <p className="scan-box-caption">
          Scan with your phone camera or in Telegram (Settings → Devices → Link Desktop or Scan QR) to join @csbites.
        </p>

        <div className="detail-top-meta">
          <a
            href="tg://resolve?domain=csbites"
            className="channel-out-link"
            title="Direct Telegram App deep link"
          >
            tg://resolve?domain=csbites ↗
          </a>
          <span>•</span>
          <a
            href="https://telegram.me/csbites"
            target="_blank"
            rel="noopener noreferrer"
            className="channel-out-link"
            title="Unblocked Telegram Web Mirror"
          >
            telegram.me/csbites ↗
          </a>
        </div>
      </aside>
    </section>
  );
}
