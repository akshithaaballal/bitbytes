import React, { useState, useEffect, useMemo, useRef } from 'react';
import { normalizeTrack, getTrackConfig, TRACK_CONFIG } from '../constants.js';
import {
  getLikedPostIds,
  togglePostLike,
  getSavedPostIds,
  togglePostSave,
  getReadPostIds,
  markPostAsRead,
  getStreakData,
  getStoredTheme,
  setStoredTheme,
} from '../utils/storage.js';

import StickyTopBar from '../components/StickyTopBar.jsx';
import ProfileHero from '../components/ProfileHero.jsx';
import StoriesRow from '../components/StoriesRow.jsx';
import StoryViewer from '../components/StoryViewer.jsx';
import PostCard from '../components/PostCard.jsx';
import ExploreGrid from '../components/ExploreGrid.jsx';
import SavedView from '../components/SavedView.jsx';
import ProfileView from '../components/ProfileView.jsx';
import BottomTabBar from '../components/BottomTabBar.jsx';
import { DesktopLeftRail, DesktopRightSidebar } from '../components/DesktopNavAndSidebar.jsx';
import PostDetailModal from '../components/PostDetailModal.jsx';

const INITIAL_PAGE_SIZE = 8;
const PAGE_STEP = 8;

export default function LandingPage({ searchInputRef, onGoToOperator }) {
  const [feedPosts, setFeedPosts] = useState([]);
  const [feedLoading, setFeedLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('feed');
  const [visibleCount, setVisibleCount] = useState(INITIAL_PAGE_SIZE);

  // Storage states
  const [likedSet, setLikedSet] = useState(() => getLikedPostIds());
  const [savedSet, setSavedSet] = useState(() => getSavedPostIds());
  const [readSet, setReadSet] = useState(() => getReadPostIds());
  const [streakData, setStreakData] = useState(() => getStreakData());
  const [currentTheme, setCurrentTheme] = useState(() => getStoredTheme());

  // Active Story Viewer
  const [activeStoryTrack, setActiveStoryTrack] = useState(null);

  // Active Post Modal (Explore grid or deep-link)
  const [activePostId, setActivePostId] = useState(() => {
    return window.location.hash.startsWith('#p/') ? window.location.hash.slice(3) : null;
  });

  const loadMoreSentinelRef = useRef(null);

  // Apply theme class to document body / root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
    setStoredTheme(currentTheme);
  }, [currentTheme]);

  function handleToggleTheme() {
    setCurrentTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }

  // Load feed.json
  useEffect(() => {
    setFeedLoading(true);
    const feedUrl = `${import.meta.env.BASE_URL}feed.json`.replace(/^\.\/\//, './');
    fetch(feedUrl)
      .then((res) => {
        if (!res.ok) {
          return fetch('/feed.json').then((r) => (r.ok ? r.json() : null));
        }
        return res.json();
      })
      .then((data) => {
        if (data && Array.isArray(data.posts)) {
          setFeedPosts(data.posts);
        }
      })
      .catch((err) => {
        console.warn('Could not load feed.json:', err);
      })
      .finally(() => {
        setFeedLoading(false);
      });
  }, []);

  // Listen for hash changes (#p/<id>)
  useEffect(() => {
    function handleHashChange() {
      const hash = window.location.hash;
      if (hash.startsWith('#p/')) {
        setActivePostId(hash.slice(3));
      } else if (!hash.startsWith('#operator')) {
        setActivePostId(null);
      }
    }
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Sync post-read events across tabs
  useEffect(() => {
    function handlePostRead(e) {
      if (e.detail?.postId) {
        setReadSet(new Set(getReadPostIds()));
      }
    }
    window.addEventListener('bitbytes:post-read', handlePostRead);
    return () => window.removeEventListener('bitbytes:post-read', handlePostRead);
  }, []);

  // Infinite scroll intersection observer for vertical feed
  useEffect(() => {
    if (activeTab !== 'feed') return;
    const sentinel = loadMoreSentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => Math.min(feedPosts.length, prev + PAGE_STEP));
        }
      },
      { rootMargin: '400px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [activeTab, feedPosts.length]);

  // Compute track metadata for Story avatars with unread counts
  const tracksMetadata = useMemo(() => {
    const keys = Object.keys(TRACK_CONFIG);
    return keys.map((trackName) => {
      const cfg = TRACK_CONFIG[trackName];
      const postsInTrack = feedPosts.filter(
        (p) => normalizeTrack(p.track) === trackName
      );
      const totalBites = postsInTrack.length;
      const unreadCount = postsInTrack.filter((p) => !readSet.has(p.id)).length;

      return {
        trackName,
        config: cfg,
        totalBites: Math.max(1, totalBites),
        unreadCount,
        posts: postsInTrack,
      };
    });
  }, [feedPosts, readSet]);

  // Find active modal post
  const modalPost = useMemo(() => {
    if (!activePostId || feedPosts.length === 0) return null;
    return (
      feedPosts.find(
        (p) => p.id === activePostId || p.id.startsWith(`${activePostId}_`)
      ) || null
    );
  }, [activePostId, feedPosts]);

  // Saved posts list
  const savedPosts = useMemo(() => {
    return feedPosts.filter((p) => savedSet.has(p.id));
  }, [feedPosts, savedSet]);

  // Handlers for likes and saves
  function handleToggleLike(postId) {
    togglePostLike(postId);
    setLikedSet(new Set(getLikedPostIds()));
  }

  function handleToggleSave(postId) {
    togglePostSave(postId);
    setSavedSet(new Set(getSavedPostIds()));
  }

  // Story selector
  function handleSelectTrackStory(trackName) {
    const trackData = tracksMetadata.find((t) => t.trackName === trackName);
    if (trackData && trackData.posts.length > 0) {
      setActiveStoryTrack(trackData);
    }
  }

  // Highlight collection clicked
  function handleSelectHighlight(highlight) {
    // Switch to Explore with filtered query or jump to first matching track
    const matching = feedPosts.filter((p) =>
      highlight.tracks.includes(normalizeTrack(p.track))
    );
    if (matching.length > 0) {
      setActivePostId(matching[0].id);
      window.location.hash = `#p/${matching[0].id}`;
    }
  }

  // Surprise Me: Jump to a random unread bite
  function handleSurpriseMe() {
    const unread = feedPosts.filter((p) => !readSet.has(p.id));
    const pool = unread.length > 0 ? unread : feedPosts;
    if (pool.length === 0) return;
    const randomPick = pool[Math.floor(Math.random() * pool.length)];
    setActivePostId(randomPick.id);
    window.location.hash = `#p/${randomPick.id}`;
    markPostAsRead(randomPick.id);
  }

  function handleOpenPostInFeed(postId) {
    setActivePostId(postId);
    window.location.hash = `#p/${postId}`;
  }

  function handleCloseModal() {
    setActivePostId(null);
    if (window.location.hash.startsWith('#p/')) {
      window.location.hash = '';
    }
  }

  return (
    <div className="instagram-layout-root">
      {/* Sticky Mobile Topbar */}
      <StickyTopBar
        currentTheme={currentTheme}
        onToggleTheme={handleToggleTheme}
        onLogoClick={() => {
          setActiveTab('feed');
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
      />

      {/* Main 3-Column Desktop Grid Layout */}
      <div className="instagram-desktop-grid">
        {/* Column 1: Desktop Left Navigation Rail */}
        <DesktopLeftRail
          activeTab={activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          savedCount={savedPosts.length}
          currentTheme={currentTheme}
          onToggleTheme={handleToggleTheme}
          onGoToOperator={onGoToOperator}
        />

        {/* Column 2: Centered 470px Mobile-First Content Column */}
        <main className="instagram-center-column">
          {/* TAB 1: HOME FEED */}
          {activeTab === 'feed' && (
            <div className="feed-tab-view">
              {/* Profile Header Hero */}
              <ProfileHero
                totalBites={feedPosts.length}
                onSelectHighlight={handleSelectHighlight}
              />

              {/* Tracks as Circular Stories Row */}
              <StoriesRow
                tracksMetadata={tracksMetadata}
                onSelectTrackStory={handleSelectTrackStory}
              />

              {/* Feed Divider */}
              <div className="feed-section-divider">
                <span className="divider-line" />
                <span className="divider-label">LATEST BITES</span>
                <span className="divider-line" />
              </div>

              {/* Vertical Carousel Feed */}
              {feedLoading ? (
                <div className="feed-loading-state">
                  <div className="loading-spinner" />
                  <span>Loading engineering notes...</span>
                </div>
              ) : (
                <div className="vertical-feed-stream">
                  {feedPosts.slice(0, visibleCount).map((post, idx) => (
                    <PostCard
                      key={post.id}
                      post={post}
                      isLiked={likedSet.has(post.id)}
                      isSaved={savedSet.has(post.id)}
                      isNew={idx < 3}
                      onToggleLike={handleToggleLike}
                      onToggleSave={handleToggleSave}
                    />
                  ))}

                  {/* Infinite Scroll Sentinel */}
                  <div ref={loadMoreSentinelRef} className="scroll-sentinel" />

                  {/* End of Feed Banner */}
                  {visibleCount >= feedPosts.length && feedPosts.length > 0 && (
                    <div className="all-caught-up-banner">
                      <span className="check-glyph">✓</span>
                      <h4>You're all caught up!</h4>
                      <p>
                        You've scrolled through all {feedPosts.length} production notes.
                        New bites drop at 8:30 AM & 8:30 PM IST.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: EXPLORE (3-Column Grid + Search) */}
          {activeTab === 'explore' && (
            <ExploreGrid
              posts={feedPosts}
              likedSet={likedSet}
              readSet={readSet}
              searchInputRef={searchInputRef}
              onSelectPost={(id) => {
                setActivePostId(id);
                window.location.hash = `#p/${id}`;
              }}
            />
          )}

          {/* TAB 3: SAVED BOOKMARKS */}
          {activeTab === 'saved' && (
            <SavedView
              savedPosts={savedPosts}
              likedSet={likedSet}
              savedSet={savedSet}
              onToggleLike={handleToggleLike}
              onToggleSave={handleToggleSave}
              onGoToFeed={() => setActiveTab('feed')}
            />
          )}

          {/* TAB 4: VISITOR PROFILE & STATS */}
          {activeTab === 'profile' && (
            <ProfileView
              totalBites={feedPosts.length}
              streakData={streakData}
              readCount={readSet.size}
              savedCount={savedPosts.length}
              likedCount={likedSet.size}
              currentTheme={currentTheme}
              onToggleTheme={handleToggleTheme}
              onSurpriseMe={handleSurpriseMe}
              onGoToOperator={onGoToOperator}
            />
          )}
        </main>

        {/* Column 3: Desktop Right Utility Sidebar */}
        <DesktopRightSidebar
          streakData={streakData}
          totalBites={feedPosts.length}
          readCount={readSet.size}
          onSurpriseMe={handleSurpriseMe}
        />
      </div>

      {/* Mobile Sticky Bottom Tab Bar */}
      <BottomTabBar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        savedCount={savedPosts.length}
      />

      {/* Full-Screen Stories Modal Viewer */}
      {activeStoryTrack && (
        <StoryViewer
          trackName={activeStoryTrack.trackName}
          posts={activeStoryTrack.posts}
          onClose={() => setActiveStoryTrack(null)}
          onOpenPostInFeed={handleOpenPostInFeed}
        />
      )}

      {/* Post Detail Modal (when opening from Explore Grid or #p/<id>) */}
      {modalPost && (
        <PostDetailModal
          post={modalPost}
          isLiked={likedSet.has(modalPost.id)}
          isSaved={savedSet.has(modalPost.id)}
          onClose={handleCloseModal}
          onToggleLike={handleToggleLike}
          onToggleSave={handleToggleSave}
        />
      )}
    </div>
  );
}
