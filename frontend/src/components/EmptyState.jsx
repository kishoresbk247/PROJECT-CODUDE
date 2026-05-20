/**
 * EmptyState.jsx — Empty state placeholder for each results tab (Day 17)
 *
 * Props:
 *   type  {string}  — 'bugs' | 'security' | 'complexity' | 'generic'
 *
 * Custom messages per tab:
 *   bugs       → "No bugs found — great code!"
 *   security   → "No vulnerabilities detected"
 *   complexity → "No functions to measure"
 *   generic    → "Nothing here yet"
 */

import './EmptyState.css';

const STATES = {
  bugs: {
    icon: '🐛',
    successIcon: '✅',
    title: 'No bugs found — great code!',
    subtitle: 'Your code passed all bug checks. Keep up the clean work.',
  },
  security: {
    icon: '🔒',
    successIcon: '🛡️',
    title: 'No vulnerabilities detected',
    subtitle: 'No known security issues found in this code snippet.',
  },
  complexity: {
    icon: '⚡',
    successIcon: '📊',
    title: 'No functions to measure',
    subtitle: 'Submit some code with functions to see complexity analysis.',
  },
  generic: {
    icon: '🔍',
    successIcon: '✨',
    title: 'Nothing here yet',
    subtitle: 'Run a review to populate this section.',
  },
};

export default function EmptyState({ type = 'generic' }) {
  const state = STATES[type] || STATES.generic;

  return (
    <div className="empty-state animate-fade-in" role="status" aria-label={state.title}>
      <div className="empty-state__icons">
        <span className="empty-state__bg-icon" aria-hidden="true">{state.icon}</span>
        <span className="empty-state__badge" aria-hidden="true">{state.successIcon}</span>
      </div>
      <h4 className="empty-state__title">{state.title}</h4>
      <p className="empty-state__subtitle">{state.subtitle}</p>
    </div>
  );
}
