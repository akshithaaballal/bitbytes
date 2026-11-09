import React from 'react';
import PostCard from './PostCard.jsx';

export default function SavedView({
  savedPosts = [],
  likedSet = new Set(),
  savedSet = new Set(),
  onToggleLike,
  onToggleSave,
  onGoToFeed,
}) {
  if (savedPosts.length === 0) {
    return (
      <div className="saved-empty-container">
        <div className="saved-empty-card">
          <span className="saved-empty-emoji">📑</span>
          <h2 className="saved-empty-title">Nothing saved yet.</h2>
          <p className="saved-empty-body">
            Go bookmark something you'll pretend to revise later.
          </p>
          <button
            type="button"
            className="btn-browse-feed"
            onClick={onGoToFeed}
          >
            Browse Feed →
          </button>
        </div>
      </div>
    );
  }

  return (
    <section className="saved-feed-container" aria-label="Saved Bookmarks">
      <div className="saved-header-banner">
        <div>
          <h2 className="saved-title">Saved Bites</h2>
          <span className="saved-count">
            {savedPosts.length} bookmarked {savedPosts.length === 1 ? 'concept' : 'concepts'}
          </span>
        </div>
      </div>

      <div className="saved-posts-list">
        {savedPosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            isLiked={likedSet.has(post.id)}
            isSaved={savedSet.has(post.id)}
            onToggleLike={onToggleLike}
            onToggleSave={onToggleSave}
          />
        ))}
      </div>
    </section>
  );
}
