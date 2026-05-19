/**
 * FindingCard.jsx — Renders a single BugFinding or SecurityFinding
 *
 * Props:
 *   finding      — { severity, message, line?, suggestion, owasp_category? }
 *   type         — 'bug' | 'security'
 *   onJumpToLine — optional callback(lineNumber)
 */

import SeverityBadge from './SeverityBadge';
import './FindingCard.css';

export default function FindingCard({ finding, type = 'bug', onJumpToLine }) {
  return (
    <div className="finding-card glass">
      <div className="finding-card__header">
        <div className="finding-card__badges">
          <SeverityBadge severity={finding.severity} />
          {type === 'security' && finding.owasp_category && (
            <span className="finding-card__owasp">{finding.owasp_category}</span>
          )}
        </div>
        {finding.line && (
          <button
            className="finding-card__jump-btn"
            onClick={() => onJumpToLine?.(finding.line)}
            title={`Jump to line ${finding.line}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
            Line {finding.line}
          </button>
        )}
      </div>
      <p className="finding-card__message">{finding.message}</p>
      {finding.suggestion && (
        <div className="finding-card__suggestion">
          <span>💡</span>
          <span><strong>Fix: </strong>{finding.suggestion}</span>
        </div>
      )}
    </div>
  );
}
