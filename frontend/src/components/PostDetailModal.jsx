import React, { useEffect } from 'react';
import PostCard from './PostCard.jsx';

export default function PostDetailModal({
  post,
  isLiked = false,
  isSaved = false,
  onClose,
  onToggleLike,
  onToggleSave,
}) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!post) return null;

  return (
    <div
      className="post-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={`Bite: ${post.title}`}
      onClick={onClose}
    >
      <div
        className="post-modal-container"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="post-modal-close-btn"
          onClick={onClose}
          aria-label="Close modal"
        >
          ✕
        </button>

        <PostCard
          post={post}
          isLiked={isLiked}
          isSaved={isSaved}
          onToggleLike={onToggleLike}
          onToggleSave={onToggleSave}
        />
      </div>
    </div>
  );
}
