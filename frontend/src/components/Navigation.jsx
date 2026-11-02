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
            href="https://github.com/akshithaaballal/bitbytes"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-link"
          >
            GitHub
          </a>

          <a
            href="https://t.me/csbites"
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
