import React, { useState, useRef, useEffect } from 'react';
import { getTrackConfig, normalizeTrack, TELEGRAM_URL } from '../constants.js';
import { buildPostSlides, formatRelativeTime, renderInlineMarkdown } from '../utils/slideParser.js';
import { TrackMotif } from './TrackMotifs.jsx';
import { togglePostLike, togglePostSave, markPostAsRead } from '../utils/storage.js';
import { exportSlideAsStory } from '../utils/storyExport.js';

export default function PostCard({
  post,
  isLiked = false,
  isSaved = false,
  isNew = false,
  onToggleLike,
  onToggleSave,
}) {
  const [activeSlide, setActiveSlide] = useState(0);
  const [captionExpanded, setCaptionExpanded] = useState(false);
  const [copyCodeSuccess, setCopyCodeSuccess] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);
  const [storyExporting, setStoryExporting] = useState(false);
  const [showHeartPop, setShowHeartPop] = useState(false);

  const touchStartXRef = useRef(null);
  const lastTapRef = useRef(0);

  const trackName = normalizeTrack(post.track);
  const trackConfig = getTrackConfig(trackName);
  const slides = buildPostSlides(post);
  const relativeTime = formatRelativeTime(post.date);

  // Mark as read when user reaches slide 2 or beyond
  useEffect(() => {
    if (activeSlide > 0) {
      markPostAsRead(post.id);
    }
  }, [activeSlide, post.id]);

  // Swipe gesture handling for mobile
  function handleTouchStart(e) {
    touchStartXRef.current = e.touches[0].clientX;
  }

  function handleTouchEnd(e) {
    if (touchStartXRef.current === null) return;
    const deltaX = e.changedTouches[0].clientX - touchStartXRef.current;
    if (deltaX < -40 && activeSlide < slides.length - 1) {
      setActiveSlide((prev) => prev + 1);
    } else if (deltaX > 40 && activeSlide > 0) {
      setActiveSlide((prev) => prev - 1);
    }
    touchStartXRef.current = null;
  }

  // Double tap to like
  function handleSlideClick(e) {
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      if (!isLiked) {
        onToggleLike(post.id);
      }
      setShowHeartPop(true);
      setTimeout(() => setShowHeartPop(false), 800);
      lastTapRef.current = 0;
      return;
    }
    lastTapRef.current = now;
  }

  function handlePrevSlide(e) {
    e.stopPropagation();
    if (activeSlide > 0) setActiveSlide((prev) => prev - 1);
  }

  function handleNextSlide(e) {
    e.stopPropagation();
    if (activeSlide < slides.length - 1) setActiveSlide((prev) => prev + 1);
  }

  // Copy code snippet to clipboard safely
  async function handleCopyCode(code) {
    try {
      await navigator.clipboard.writeText(code);
      setCopyCodeSuccess(true);
      setTimeout(() => setCopyCodeSuccess(false), 2000);
    } catch {
      // Fallback
    }
  }

  // Native share or copy link
  async function handleSharePost() {
    const shareUrl = `${window.location.origin}${window.location.pathname}#p/${post.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: `BitBytes: ${post.title}`,
          text: `Read this bite on ${trackConfig.label}: "${post.title}"`,
          url: shareUrl,
        });
        return;
      } catch {}
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 2000);
    } catch {}
  }

  // Export 1080x1920 Story PNG
  async function handleExportStory() {
    setStoryExporting(true);
    try {
      await exportSlideAsStory(post, activeSlide);
    } finally {
      setStoryExporting(false);
    }
  }

  const currentSlideData = slides[activeSlide] || slides[0];

  return (
    <article className="post-card" aria-label={`Bite: ${post.title}`}>
      {/* Rotated NEW Sticker */}
      {isNew && (
        <div className="post-sticker-new" aria-label="New Post">
          NEW
        </div>
      )}

      {/* Post Chrome Header */}
      <header className="post-chrome-header">
        <div className="post-author-box">
          <div
            className="post-avatar-ring"
            style={{ borderColor: trackConfig.color }}
          >
            <span
              className="post-avatar-inner"
              style={{ backgroundColor: trackConfig.bgTint, color: trackConfig.color }}
            >
              ⚡
            </span>
          </div>

          <div className="post-meta-text">
            <div className="post-meta-line-1">
              <span className="post-username">csbites</span>
              <span className="post-bullet">•</span>
              <span
                className="post-track-badge"
                style={{
                  color: trackConfig.color,
                  backgroundColor: trackConfig.bgTint,
                  borderColor: trackConfig.color,
                }}
              >
                {trackConfig.shortLabel}
              </span>
            </div>
            <span className="post-timestamp">{relativeTime}</span>
          </div>
        </div>

        {/* Slide Counter Pill (e.g. 1/5) */}
        <div className="post-slide-counter">
          {activeSlide + 1}/{slides.length}
        </div>
      </header>

      {/* Swipeable Carousel Slide Stage */}
      <div
        className="carousel-stage"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onClick={handleSlideClick}
        style={{ borderTopColor: trackConfig.color }}
      >
        {/* Heart Pop on Double Tap */}
        {showHeartPop && (
          <div className="heart-pop-burst" aria-hidden="true">
            ❤️
          </div>
        )}

        {/* Desktop Click Zone & Chevron: Left */}
        {activeSlide > 0 && (
          <button
            type="button"
            className="carousel-nav-btn btn-left"
            onClick={handlePrevSlide}
            aria-label="Previous slide"
          >
            ‹
          </button>
        )}

        {/* Desktop Click Zone & Chevron: Right */}
        {activeSlide < slides.length - 1 && (
          <button
            type="button"
            className="carousel-nav-btn btn-right"
            onClick={handleNextSlide}
            aria-label="Next slide"
          >
            ›
          </button>
        )}

        {/* SLIDE 1: HOOK / SCENARIO COVER */}
        {currentSlideData.type === 'hook' && (
          <div className="slide-content slide-hook">
            <div className="slide-motif-watermark" aria-hidden="true">
              <TrackMotif trackName={trackName} />
            </div>

            <div className="slide-hook-tagline">
              <span className="hook-pill" style={{ backgroundColor: trackConfig.color }}>
                THE HOOK
              </span>
              <span className="hook-est-time">{post.read_minutes || 1} min read</span>
            </div>

            <h3 className="slide-hook-question">
              "{currentSlideData.hook}"
            </h3>

            <div className="slide-hook-topic-box">
              <span className="topic-prefix">TOPIC:</span>
              <span className="topic-name">{post.title}</span>
            </div>

            <div className="slide-hook-swipe-hint">
              <span>Swipe to unpack</span>
              <span className="arrow-pulse">→</span>
            </div>
          </div>
        )}

        {/* SLIDE 2: MENTAL MODEL EXPLANATION + DIAGRAM */}
        {currentSlideData.type === 'mental_model' && (
          <div className="slide-content slide-mental-model">
            <div className="slide-section-header">
              <span className="section-pill" style={{ color: trackConfig.color }}>
                MENTAL MODEL
              </span>
            </div>

            <p className="slide-explanation-text">
              {renderInlineMarkdown(currentSlideData.text)}
            </p>

            {/* Hand-Drawn Wobbly SVG Diagram */}
            <div className="slide-diagram-card">
              <TrackMotif trackName={trackName} className="slide-diagram-svg" />
            </div>
          </div>
        )}

        {/* SLIDE 3: CODE SNIPPET (OR KEY POINTS) */}
        {currentSlideData.type === 'code' && (
          <div className="slide-content slide-code">
            <div className="slide-code-topbar">
              <span className="code-lang-tag" style={{ color: trackConfig.color }}>
                // PRODUCTION PATTERN
              </span>
              <button
                type="button"
                className="btn-copy-code"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCopyCode(currentSlideData.code);
                }}
              >
                {copyCodeSuccess ? '✓ Copied' : 'Copy'}
              </button>
            </div>

            <div className="slide-code-block">
              <pre>
                <code>
                  {currentSlideData.code.split('\n').map((line, idx) => (
                    <div key={idx} className="code-line">
                      <span className="line-num">{idx + 1}</span>
                      <span className="line-text">{line}</span>
                    </div>
                  ))}
                </code>
              </pre>
            </div>
          </div>
        )}

        {currentSlideData.type === 'key_points' && (
          <div className="slide-content slide-points">
            <div className="slide-section-header">
              <span className="section-pill" style={{ color: trackConfig.color }}>
                ARCHITECTURAL MECHANISM
              </span>
            </div>

            <ul className="slide-points-list">
              {currentSlideData.points.map((pt, idx) => (
                <li key={idx} className="slide-point-item">
                  <span className="point-bullet" style={{ color: trackConfig.color }}>
                    0{idx + 1}
                  </span>
                  <span className="point-text">{renderInlineMarkdown(pt)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* SLIDE 4: COMPLEXITY & INTERVIEW TIP */}
        {currentSlideData.type === 'complexity' && (
          <div className="slide-content slide-complexity">
            <div className="slide-section-header">
              <span className="section-pill" style={{ color: trackConfig.color }}>
                SYSTEMS COMPLEXITY
              </span>
            </div>

            {currentSlideData.complexityEntries.length > 0 && (
              <div className="complexity-grid">
                {currentSlideData.complexityEntries.map(([k, v]) => (
                  <div key={k} className="complexity-cell">
                    <span className="complexity-key">{k.replace(/_/g, ' ')}</span>
                    <span className="complexity-val" style={{ color: trackConfig.color }}>
                      {String(v)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {currentSlideData.interviewTip && (
              <div className="interview-tip-box" style={{ borderColor: trackConfig.color }}>
                <span className="tip-badge" style={{ backgroundColor: trackConfig.color }}>
                  INTERVIEW MENTAL MODEL
                </span>
                <p className="tip-text">"{currentSlideData.interviewTip}"</p>
              </div>
            )}
          </div>
        )}

        {/* SLIDE 5: SOURCE & ACTION */}
        {currentSlideData.type === 'source' && (
          <div className="slide-content slide-source">
            <div className="slide-section-header">
              <span className="section-pill" style={{ color: trackConfig.color }}>
                SOURCE & DISCUSSION
              </span>
            </div>

            <div className="source-domain-card">
              <span className="source-label">VERIFIED SOURCE:</span>
              <a
                href={currentSlideData.source.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="source-title-link"
                onClick={(e) => e.stopPropagation()}
              >
                {currentSlideData.source.domain || 'Engineering Notebook'} ↗
              </a>
              <span className="source-full-title">
                {currentSlideData.source.title}
              </span>
            </div>

            <div className="source-actions-group">
              <a
                href={currentSlideData.telegramUrl || TELEGRAM_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-discuss-telegram"
                style={{ backgroundColor: trackConfig.color }}
                onClick={(e) => e.stopPropagation()}
              >
                Discuss on Telegram ✈
              </a>

              <button
                type="button"
                className="btn-slide-share-story"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExportStory();
                }}
                disabled={storyExporting}
              >
                {storyExporting ? 'Generating...' : 'Share as Story (PNG) ⇪'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Dot Pagination Bar */}
      <div className="carousel-dots-row" aria-label="Slide pagination">
        {slides.map((_, idx) => (
          <button
            key={idx}
            type="button"
            className={`carousel-dot ${activeSlide === idx ? 'is-active' : ''}`}
            onClick={() => setActiveSlide(idx)}
            aria-label={`Go to slide ${idx + 1}`}
            style={{
              backgroundColor: activeSlide === idx ? trackConfig.color : undefined,
            }}
          />
        ))}
      </div>

      {/* Action Row */}
      <div className="post-actions-row">
        <div className="post-actions-left">
          {/* Like Button */}
          <button
            type="button"
            className={`btn-action-icon btn-like ${isLiked ? 'active' : ''}`}
            onClick={() => onToggleLike(post.id)}
            aria-label={isLiked ? 'Unlike note' : 'Like note'}
          >
            <span className="action-icon-glyph">{isLiked ? '❤️' : '🤍'}</span>
          </button>

          {/* Save / Bookmark Button */}
          <button
            type="button"
            className={`btn-action-icon btn-save ${isSaved ? 'active' : ''}`}
            onClick={() => onToggleSave(post.id)}
            aria-label={isSaved ? 'Unsave note' : 'Save note'}
          >
            <span className="action-icon-glyph">{isSaved ? '🔖' : '📑'}</span>
          </button>

          {/* Share Button */}
          <button
            type="button"
            className="btn-action-icon btn-share"
            onClick={handleSharePost}
            aria-label="Share note"
          >
            <span className="action-icon-glyph">{shareSuccess ? '✓' : '↗'}</span>
          </button>

          {/* Quick Story Export */}
          <button
            type="button"
            className="btn-action-pill"
            onClick={handleExportStory}
            disabled={storyExporting}
            aria-label="Export as story image"
          >
            {storyExporting ? 'Exporting...' : 'Story PNG'}
          </button>
        </div>

        <div className="post-actions-right">
          <a
            href={post.telegram_url || TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-telegram-link"
            aria-label="Open note in Telegram"
          >
            Telegram ↗
          </a>
        </div>
      </div>

      {/* Caption Area (First line bold + 'more' to expand) */}
      <div className="post-caption-box">
        <p className="caption-text">
          <strong className="caption-username">csbites</strong>{' '}
          <span className="caption-lead">
            {currentSlideData.hook || post.title}
          </span>
          {captionExpanded ? (
            <span className="caption-body">
              {' '}
              {post.summary}
              <button
                type="button"
                className="btn-caption-toggle"
                onClick={() => setCaptionExpanded(false)}
              >
                less
              </button>
            </span>
          ) : (
            <button
              type="button"
              className="btn-caption-toggle"
              onClick={() => setCaptionExpanded(true)}
            >
              ...more
            </button>
          )}
        </p>

        {/* Tag pills */}
        <div className="caption-tags">
          <span className="caption-tag">{trackConfig.tag}</span>
          <span className="caption-tag">#BitBytes</span>
          <span className="caption-tag">#SystemsCS</span>
        </div>
      </div>
    </article>
  );
}
