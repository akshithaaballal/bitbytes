import { useState, useEffect, useRef } from 'react';
import Navigation from './components/Navigation.jsx';
import LandingPage from './pages/LandingPage.jsx';
import Dashboard from './pages/Dashboard.jsx';
import OperatorLogin from './components/OperatorLogin.jsx';

export default function App() {
  const [currentView, setCurrentView] = useState('landing');
  const searchInputRef = useRef(null);

  // Focus search input on '/' shortcut (ignoring modifier keys, inputs, textareas, selects, and contenteditable)
  useEffect(() => {
    function handleKeyDown(e) {
      if (
        e.key === '/' &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        !e.shiftKey
      ) {
        const el = document.activeElement;
        const tag = el?.tagName;
        if (
          tag === 'INPUT' ||
          tag === 'TEXTAREA' ||
          tag === 'SELECT' ||
          el?.isContentEditable
        ) {
          return;
        }
        e.preventDefault();
        if (currentView !== 'landing') {
          setCurrentView('landing');
        }
        if (window.location.hash.startsWith('#p/')) {
          window.location.hash = '';
        }
        setTimeout(() => {
          searchInputRef.current?.focus();
          searchInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 50);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentView]);

  // Check URL hash on load and changes
  useEffect(() => {
    function syncHash() {
      const isOperatorHash = window.location.hash === '#operator' || window.location.pathname === '/operator';
      const isAuthed = sessionStorage.getItem('bitbytes_operator_auth') === 'true';

      if (isOperatorHash) {
        if (isAuthed) {
          setCurrentView('operator_console');
        } else {
          setCurrentView('operator_login');
        }
      } else if (!window.location.hash.startsWith('#p/')) {
        // If not operator and not post detail, stay on landing
        if (currentView === 'operator_console' || currentView === 'operator_login') {
          // If explicitly on operator view, keep it unless hash cleared
          if (window.location.hash === '') {
            setCurrentView('landing');
          }
        }
      }
    }

    syncHash();
    window.addEventListener('hashchange', syncHash);
    return () => window.removeEventListener('hashchange', syncHash);
  }, [currentView]);

  function handleGoToOperator() {
    const isAuthed = sessionStorage.getItem('bitbytes_operator_auth') === 'true';
    window.location.hash = '#operator';
    if (isAuthed) {
      setCurrentView('operator_console');
    } else {
      setCurrentView('operator_login');
    }
  }

  function handleLogout() {
    sessionStorage.removeItem('bitbytes_operator_auth');
    sessionStorage.removeItem('bitbytes_operator_token');
    window.location.hash = '';
    setCurrentView('landing');
  }

  function handleFocusSearch() {
    if (currentView !== 'landing') {
      setCurrentView('landing');
    }
    if (window.location.hash.startsWith('#p/')) {
      window.location.hash = '';
    }
    setTimeout(() => {
      searchInputRef.current?.focus();
      searchInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 50);
  }

  return (
    <div className="app-root">
      {/* Navigation Header */}
      <Navigation onFocusSearch={handleFocusSearch} />

      {/* Public Landing View */}
      {currentView === 'landing' && (
        <LandingPage
          searchInputRef={searchInputRef}
          onGoToOperator={handleGoToOperator}
        />
      )}

      {/* Operator Gateway */}
      {currentView === 'operator_login' && (
        <main className="page-container">
          <OperatorLogin
            onLoginSuccess={() => {
              sessionStorage.setItem('bitbytes_operator_auth', 'true');
              window.location.hash = '#operator';
              setCurrentView('operator_console');
            }}
            onCancel={() => {
              window.location.hash = '';
              setCurrentView('landing');
            }}
          />
        </main>
      )}

      {/* Operator Dashboard Console */}
      {currentView === 'operator_console' && (
        <main className="page">
          <div className="console-banner">
            <div>
              <span className="console-badge">AUTHENTICATED OPERATOR PORTAL</span>
              <h1 className="console-title">Operator Console & Telemetry</h1>
              <p className="console-sub">Direct control over the broadcast pipeline and audit logs.</p>
            </div>
            <div className="console-banner-actions">
              <button
                type="button"
                className="btn-back-landing"
                onClick={() => {
                  window.location.hash = '';
                  setCurrentView('landing');
                }}
              >
                View Public Page
              </button>
              <button
                type="button"
                className="btn-logout-operator"
                onClick={handleLogout}
              >
                Lock Session
              </button>
            </div>
          </div>
          <Dashboard />
        </main>
      )}
    </div>
  );
}
