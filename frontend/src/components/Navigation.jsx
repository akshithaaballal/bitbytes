import { GITHUB_REPO_URL, TELEGRAM_URL } from '../constants.js';

export default function Navigation({ onFocusSearch }) {
  function handleBrandClick(e) {
    e.preventDefault();
    if (window.location.hash) {
      window.location.hash = '';
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <header className="site-nav">
      <div className="nav-inner">
        <div className="nav-brand-group">
          <a
            href="#"
            className="nav-title"
            onClick={handleBrandClick}
            title="Return to BitBytes home"
          >
            BitBytes
          </a>
          <span className="nav-meta">Daily systems engineering notes</span>
        </div>

        <nav className="nav-actions" aria-label="Quick links">
          <button
            type="button"
            className="nav-link"
            onClick={onFocusSearch}
            title="Focus topic search (/)"
          >
            Search <span className="nav-shortcut-hint">/</span>
          </button>

          <a
            href={GITHUB_REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="nav-link"
          >
            GitHub
          </a>

          <a
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-nav-primary"
          >
            Join @csbites
          </a>
        </nav>
      </div>
    </header>
  );
}
