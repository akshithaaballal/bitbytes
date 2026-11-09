import React from 'react';

export default function BottomTabBar({
  activeTab = 'feed',
  onTabChange,
  savedCount = 0,
}) {
  const tabs = [
    {
      id: 'feed',
      label: 'Home',
      icon: (
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.3">
          <path d="M3 10l9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10z" />
          <path d="M9 21V12h6v9" />
        </svg>
      ),
    },
    {
      id: 'explore',
      label: 'Explore',
      icon: (
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.3">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
      ),
    },
    {
      id: 'saved',
      label: 'Saved',
      badge: savedCount > 0 ? savedCount : null,
      icon: (
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.3">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.3">
          <circle cx="12" cy="7" r="4" />
          <path d="M5.5 21a6.5 6.5 0 0 1 13 0" />
        </svg>
      ),
    },
  ];

  return (
    <nav className="bottom-tab-bar" aria-label="Main Navigation">
      <div className="bottom-tab-bar-inner">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              className={`bottom-tab-btn ${isActive ? 'is-active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              aria-label={tab.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="tab-icon-wrap">
                {tab.icon}
                {tab.badge && <span className="tab-badge-pill">{tab.badge}</span>}
              </div>
              <span className="tab-label-text">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
