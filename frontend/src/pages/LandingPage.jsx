import { useState, useEffect } from 'react';
import JoinHero from '../components/JoinHero.jsx';
import NewsCoverageSection from '../components/NewsCoverageSection.jsx';
import NoteDetailView from '../components/NoteDetailView.jsx';

export default function LandingPage({ searchInputRef, onGoToOperator }) {
  const [activePostId, setActivePostId] = useState(() => {
    return window.location.hash.startsWith('#p/') ? window.location.hash.slice(3) : null;
  });
  const [activePost, setActivePost] = useState(null);
  const [feedPosts, setFeedPosts] = useState([]);

  useEffect(() => {
    fetch('/feed.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && Array.isArray(data.posts)) {
          setFeedPosts(data.posts);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleHashChange() {
      const hash = window.location.hash;
      if (hash.startsWith('#p/')) {
        const id = hash.slice(3);
        setActivePostId(id);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        setActivePostId(null);
      }
    }

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    if (activePostId && feedPosts.length > 0) {
      const found = feedPosts.find((p) => p.id === activePostId);
      setActivePost(found || null);
    } else {
      setActivePost(null);
    }
  }, [activePostId, feedPosts]);

  function handleBackToFeed() {
    window.location.hash = '';
    setActivePostId(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <main className="page-container">
      {activePostId ? (
        <NoteDetailView post={activePost} onBack={handleBackToFeed} />
      ) : (
        <>
          <JoinHero />
          <NewsCoverageSection
            searchInputRef={searchInputRef}
            onSelectPost={(id) => setActivePostId(id)}
          />
        </>
      )}

      {/* Human Editorial Footer */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-left">
            <strong>BitBytes</strong>
            <span className="footer-desc">
              An open notebook for B.Tech computer science students and engineers. No tracking. No marketing emails. No sponsored noise.
            </span>
          </div>

          <div className="footer-links">
            <a
              href="https://t.me/csbites"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-link"
            >
              Telegram channel
            </a>
            <span className="footer-link" aria-hidden="true">•</span>
            <a
              href="https://github.com/akshithaaballal/bitbytes"
              target="_blank"
              rel="noopener noreferrer"
              className="footer-link"
            >
              GitHub repo
            </a>
            <span className="footer-link" aria-hidden="true">•</span>
            <button
              type="button"
              className="footer-operator-btn"
              onClick={onGoToOperator}
              title="Operator Gateway login"
            >
              Operator portal
            </button>
          </div>
        </div>
      </footer>
    </main>
  );
}
