/**
 * ErrorBanner.jsx — Dismissable error banner (Day 17)
 *
 * Props:
 *   error      {string}   — the error message to display
 *   onDismiss  {function} — called when the × button is clicked
 *   onRetry    {function} — called when "Try again" is clicked (optional)
 *
 * Design: red-tinted glassmorphism card with slide-in animation.
 * Accessible: role="alert" so screen-readers announce it immediately.
 */

import './ErrorBanner.css';

export default function ErrorBanner({ error, onDismiss, onRetry }) {
  if (!error) return null;

  return (
    <div className="error-banner-v2 animate-slide-up" role="alert" id="error-banner">
      <span className="error-banner-v2__icon" aria-hidden="true">⚠️</span>

      <div className="error-banner-v2__body">
        <span className="error-banner-v2__title">Something went wrong</span>
        <span className="error-banner-v2__message">{error}</span>
      </div>

      <div className="error-banner-v2__actions">
        {onRetry && (
          <button
            className="error-banner-v2__retry"
            onClick={onRetry}
            id="error-retry-button"
          >
            ↺ Try again
          </button>
        )}
        {onDismiss && (
          <button
            className="error-banner-v2__dismiss"
            onClick={onDismiss}
            aria-label="Dismiss error"
            id="error-dismiss-button"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
