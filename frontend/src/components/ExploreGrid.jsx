import React, { useState, useMemo } from 'react';
import { normalizeTrack, getTrackConfig, TRACK_CONFIG } from '../constants.js';
import { TrackMotif } from './TrackMotifs.jsx';

export default function ExploreGrid({
  posts = [],
  likedSet = new Set(),
  readSet = new Set(),
  onSelectPost,
  searchInputRef,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTrackFilter, setSelectedTrackFilter] = useState('ALL');

  const filteredPosts = useMemo(() => {
    let result = posts;

    if (selectedTrackFilter !== 'ALL') {
      result = result.filter(
        (p) => normalizeTrack(p.track) === selectedTrackFilter
      );
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter((p) => {
        const title = (p.title || '').toLowerCase();
        const subtitle = (p.subtitle || '').toLowerCase();
        const track = (p.track || '').toLowerCase();
        const domain = (p.source?.domain || '').toLowerCase();
        const summary = (p.summary || '').toLowerCase();
        return (
          title.includes(q) ||
          subtitle.includes(q) ||
          track.includes(q) ||
          domain.includes(q) ||
          summary.includes(q)
        );
      });
    }

    return result;
  }, [posts, selectedTrackFilter, searchQuery]);

  const trackKeys = Object.keys(TRACK_CONFIG);

  return (
    <section className="explore-grid-container" aria-label="Explore Notes">
      {/* Search Input Bar */}
      <div className="explore-search-bar">
        <span className="search-icon-glyph">⚲</span>
        <input
          ref={searchInputRef}
          type="search"
          className="explore-search-input"
          placeholder="Search by topic, track, or domain (Press /)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Search technical concepts"
        />
        {searchQuery && (
          <button
            type="button"
            className="search-clear-btn"
            onClick={() => setSearchQuery('')}
          >
            ✕
          </button>
        )}
      </div>

      {/* Track Filter Filter Chips */}
      <div className="explore-filter-strip">
        <button
          type="button"
          className={`filter-chip ${selectedTrackFilter === 'ALL' ? 'active' : ''}`}
          onClick={() => setSelectedTrackFilter('ALL')}
        >
          All ({posts.length})
        </button>
        {trackKeys.map((track) => {
          const cfg = TRACK_CONFIG[track];
          const count = posts.filter((p) => normalizeTrack(p.track) === track).length;
          return (
            <button
              key={track}
              type="button"
              className={`filter-chip ${selectedTrackFilter === track ? 'active' : ''}`}
              onClick={() => setSelectedTrackFilter(track)}
              style={{
                borderColor: selectedTrackFilter === track ? cfg.color : undefined,
                color: selectedTrackFilter === track ? cfg.color : undefined,
              }}
            >
              {cfg.shortLabel} ({count})
            </button>
          );
        })}
      </div>

      {/* 3-Column Square Tile Grid */}
      {filteredPosts.length === 0 ? (
        <div className="explore-empty-state">
          <p className="empty-title">No bites found for "{searchQuery}"</p>
          <span className="empty-sub">Try searching for "lock", "memory", "consensus", or clear your filter.</span>
          <button
            type="button"
            className="btn-clear-search"
            onClick={() => {
              setSearchQuery('');
              setSelectedTrackFilter('ALL');
            }}
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="explore-square-grid">
          {filteredPosts.map((post) => {
            const track = normalizeTrack(post.track);
            const cfg = getTrackConfig(track);
            const isLiked = likedSet.has(post.id);
            const isRead = readSet.has(post.id);

            return (
              <button
                key={post.id}
                type="button"
                className={`explore-tile ${isRead ? 'is-read' : ''}`}
                onClick={() => onSelectPost(post.id)}
                style={{ borderTopColor: cfg.color }}
                aria-label={`Open ${post.title}`}
              >
                {/* Track Motif Icon in background */}
                <div className="tile-motif-watermark" aria-hidden="true">
                  <TrackMotif trackName={track} />
                </div>

                {/* Top Tile Badge */}
                <div className="tile-top-bar">
                  <span
                    className="tile-track-tag"
                    style={{ backgroundColor: cfg.color }}
                  >
                    {cfg.shortLabel}
                  </span>
                  <span className="tile-multi-icon" title="Carousel note">
                    ⧉ 5
                  </span>
                </div>

                {/* Center Title */}
                <div className="tile-title-box">
                  <span className="tile-title-text">{post.title}</span>
                </div>

                {/* Bottom Tile Meta */}
                <div className="tile-bottom-bar">
                  {isLiked && <span className="tile-heart-glyph">❤️</span>}
                  <span className="tile-read-time">{post.read_minutes || 1}m</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
