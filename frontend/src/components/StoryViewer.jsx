import React, { useState, useEffect, useRef } from 'react';
import { getTrackConfig } from '../constants.js';
import { TrackMotif } from './TrackMotifs.jsx';
import { markPostAsRead, togglePostLike, togglePostSave, getLikedPostIds, getSavedPostIds } from '../utils/storage.js';
import { getPostHook, extractCoreExplanation, renderInlineMarkdown } from '../utils/slideParser.js';

const STORY_DURATION_MS = 6000;

export default function StoryViewer({
  trackName,
  posts = [],
  onClose,
  onOpenPostInFeed,
}) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const [liked, setLiked] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showHeartPop, setShowHeartPop] = useState(false);

  const timerRef = useRef(null);
  const startTimeRef = useRef(Date.now());
  const elapsedBeforePauseRef = useRef(0);
  const touchStartYRef = useRef(null);
  const lastTapTimeRef = useRef(0);

  const activePost = posts[currentIndex] || posts[0];
  const trackConfig = getTrackConfig(trackName);

  // Sync like and save status on slide change
  useEffect(() => {
    if (!activePost) return;
    const likes = getLikedPostIds();
    const saves = getSavedPostIds();
    setLiked(likes.has(activePost.id));
    setSaved(saves.has(activePost.id));

    // Mark active bite as read
    markPostAsRead(activePost.id);
  }, [activePost]);

  // Handle timer & smooth progress bar
  useEffect(() => {
    if (!activePost || isPaused) return;

    const intervalTime = 50;
    const totalDuration = STORY_DURATION_MS;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + (intervalTime / totalDuration) * 100;
        if (next >= 100) {
          handleNextBite();
          return 0;
        }
        return next;
      });
    }, intervalTime);

    return () => clearInterval(interval);
  }, [currentIndex, isPaused, activePost]);

  function handleNextBite() {
    setProgress(0);
    elapsedBeforePauseRef.current = 0;
    if (currentIndex < posts.length - 1) {
      setCurrentIndex((i) => i + 1);
    } else {
      // Reached end of track stories
      onClose();
    }
  }

  function handlePrevBite() {
    setProgress(0);
    elapsedBeforePauseRef.current = 0;
    if (progress > 25) {
      // Restart current bite
      setProgress(0);
    } else if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
    }
  }

  // Keyboard navigation
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        handleNextBite();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrevBite();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, progress, posts]);

  // Touch and hold-to-pause
  function handlePointerDown(e) {
    setIsPaused(true);
  }

  function handlePointerUp(e) {
    setIsPaused(false);
  }

  // Swipe down to close
  function handleTouchStart(e) {
    touchStartYRef.current = e.touches[0].clientY;
  }

  function handleTouchEnd(e) {
    if (touchStartYRef.current === null) return;
    const deltaY = e.changedTouches[0].clientY - touchStartYRef.current;
    if (deltaY > 80) {
      onClose();
    }
    touchStartYRef.current = null;
  }

  // Double tap to like
  function handleTapScreen(e) {
    const now = Date.now();
    if (now - lastTapTimeRef.current < 300) {
      // Double tap detected
      if (activePost) {
        togglePostLike(activePost.id);
        setLiked(true);
        setShowHeartPop(true);
        setTimeout(() => setShowHeartPop(false), 800);
      }
      lastTapTimeRef.current = 0;
      return;
    }
    lastTapTimeRef.current = now;

    // Tap left 30% vs right 70%
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    if (clickX < rect.width * 0.3) {
      handlePrevBite();
    } else {
      handleNextBite();
    }
  }

  if (!activePost) return null;

  const hook = getPostHook(activePost);
  const coreText = extractCoreExplanation(activePost.summary);

  return (
    <div
      className="story-viewer-modal"
      role="dialog"
      aria-modal="true"
      aria-label={`${trackName} stories`}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      <div className="story-card-container">
        {/* Top Progress Bars Strip (one per bite) */}
        <div className="story-progress-strip">
          {posts.map((post, idx) => {
            let widthPercent = 0;
            if (idx < currentIndex) widthPercent = 100;
            else if (idx === currentIndex) widthPercent = progress;

            return (
              <div key={post.id || idx} className="story-progress-track">
                <div
                  className="story-progress-fill"
                  style={{
                    width: `${widthPercent}%`,
                    backgroundColor: trackConfig.color,
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Story Header */}
        <div className="story-viewer-header">
          <div className="story-header-author">
            <span
              className="story-header-badge"
              style={{ backgroundColor: trackConfig.color }}
            >
              {trackConfig.shortLabel.slice(0, 3)}
            </span>
            <div>
              <div className="story-header-title">
                <strong>csbites</strong>
                <span className="story-header-sep">•</span>
                <span style={{ color: trackConfig.color }}>{trackConfig.shortLabel}</span>
              </div>
              <span className="story-header-sub">
                Bite {currentIndex + 1} of {posts.length}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="story-close-btn"
            onClick={onClose}
            aria-label="Close story"
          >
            ✕
          </button>
        </div>

        {/* Story Content Area (Tappable Left / Right with Hold-to-pause) */}
        <div
          className="story-card-body"
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onClick={handleTapScreen}
          style={{ borderTopColor: trackConfig.color }}
        >
          {/* Heart Pop Animation on Double-Tap */}
          {showHeartPop && (
            <div className="story-heart-pop" aria-hidden="true">
              ❤️
            </div>
          )}

          {/* Track Motif Background Watermark */}
          <div className="story-motif-bg" aria-hidden="true">
            <TrackMotif trackName={trackName} />
          </div>

          <div className="story-content-wrap">
            <div
              className="story-track-pill"
              style={{
                backgroundColor: trackConfig.bgTint,
                color: trackConfig.color,
                borderColor: trackConfig.color,
              }}
            >
              {trackConfig.label}
            </div>

            <h2 className="story-title">{activePost.title}</h2>

            <div className="story-hook-box" style={{ borderColor: trackConfig.color }}>
              <span className="story-hook-tag" style={{ color: trackConfig.color }}>
                THE HOOK
              </span>
              <p className="story-hook-text">"{hook}"</p>
            </div>

            <p className="story-summary-text">
              {renderInlineMarkdown(coreText.slice(0, 220))}
              {coreText.length > 220 ? '...' : ''}
            </p>

            {activePost.code_snippet && (
              <div className="story-mini-code">
                <span className="mini-code-tag">// CODE EXCERPT</span>
                <pre>{activePost.code_snippet.split('\n').slice(0, 3).join('\n')}</pre>
              </div>
            )}
          </div>
        </div>

        {/* Story Footer Actions */}
        <div className="story-viewer-footer">
          <button
            type="button"
            className={`story-action-btn ${liked ? 'is-liked' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              togglePostLike(activePost.id);
              setLiked(!liked);
            }}
            aria-label={liked ? 'Unlike note' : 'Like note'}
          >
            {liked ? '❤️' : '🤍'}
          </button>

          <button
            type="button"
            className={`story-action-btn ${saved ? 'is-saved' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              togglePostSave(activePost.id);
              setSaved(!saved);
            }}
            aria-label={saved ? 'Unsave note' : 'Save note'}
          >
            {saved ? '🔖' : '📑'}
          </button>

          <button
            type="button"
            className="story-feed-link-btn"
            onClick={(e) => {
              e.stopPropagation();
              onOpenPostInFeed(activePost.id);
              onClose();
            }}
          >
            View Full Post →
          </button>
        </div>
      </div>
    </div>
  );
}
