/**
 * ResultsTabs.jsx — Tabbed interface for review results
 *
 * Four tabs: Overview, Bugs, Security, Complexity.
 * Each tab header shows a count badge with color-coded severity summary.
 *
 * Props:
 *   result       — the full CodeReviewResponse object
 *   onJumpToLine — callback(lineNumber) forwarded to FindingCards
 */

import { useState } from 'react';
import FindingCard from './FindingCard';
import ScoreGauge from './ScoreGauge';
import ComplexityChart from './ComplexityChart';
import './ResultsTabs.css';

const TABS = [
  { key: 'overview',   label: 'Overview',    icon: '📊' },
  { key: 'bugs',       label: 'Bugs',        icon: '🐛' },
  { key: 'security',   label: 'Security',    icon: '🔒' },
  { key: 'complexity', label: 'Complexity',  icon: '⚡' },
];

function countBySeverity(items = []) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  items.forEach((item) => {
    if (counts[item.severity] !== undefined) counts[item.severity]++;
  });
  return counts;
}

function SeverityDots({ items }) {
  const counts = countBySeverity(items);
  return (
    <div className="tabs__severity-dots">
      {counts.critical > 0 && <span className="dot dot--critical">{counts.critical}</span>}
      {counts.high > 0 && <span className="dot dot--high">{counts.high}</span>}
      {counts.medium > 0 && <span className="dot dot--medium">{counts.medium}</span>}
      {counts.low > 0 && <span className="dot dot--low">{counts.low}</span>}
    </div>
  );
}

export default function ResultsTabs({ result, onJumpToLine }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!result) return null;

  const bugs = result.bugs || [];
  const security = result.security || [];
  const complexity = result.complexity;
  const complexityScores = complexity?.complexity_scores || [];

  function getTabCount(key) {
    if (key === 'bugs') return bugs.length;
    if (key === 'security') return security.length;
    if (key === 'complexity') return complexityScores.length;
    return null;
  }

  function getTabItems(key) {
    if (key === 'bugs') return bugs;
    if (key === 'security') return security;
    return [];
  }

  return (
    <div className="results-tabs" id="results-tabs">
      {/* Tab Headers */}
      <div className="results-tabs__header">
        {TABS.map((tab) => {
          const count = getTabCount(tab.key);
          return (
            <button
              key={tab.key}
              className={`results-tabs__tab ${activeTab === tab.key ? 'results-tabs__tab--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
              id={`tab-${tab.key}`}
            >
              <span className="results-tabs__tab-icon">{tab.icon}</span>
              <span>{tab.label}</span>
              {count !== null && count > 0 && (
                <span className="results-tabs__count">{count}</span>
              )}
              {(tab.key === 'bugs' || tab.key === 'security') && (
                <SeverityDots items={getTabItems(tab.key)} />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="results-tabs__content">
        {/* Overview */}
        {activeTab === 'overview' && (
          <div className="tab-panel animate-fade-in" id="panel-overview">
            <div className="overview-top">
              <ScoreGauge score={result.overall_score} />
              <div className="overview-summary">
                <h3 className="overview-summary__title">Analysis Summary</h3>
                <p className="overview-summary__text">{result.summary}</p>
                <div className="overview-stats">
                  <div className="overview-stat">
                    <span className="overview-stat__value">{bugs.length}</span>
                    <span className="overview-stat__label">Bugs</span>
                  </div>
                  <div className="overview-stat">
                    <span className="overview-stat__value">{security.length}</span>
                    <span className="overview-stat__label">Security</span>
                  </div>
                  <div className="overview-stat">
                    <span className="overview-stat__value">{complexityScores.length}</span>
                    <span className="overview-stat__label">Functions</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bugs */}
        {activeTab === 'bugs' && (
          <div className="tab-panel animate-fade-in" id="panel-bugs">
            {bugs.length === 0 ? (
              <div className="tab-panel__empty">
                <span>✅</span> No bugs detected
              </div>
            ) : (
              <div className="findings-list">
                {bugs.map((bug, i) => (
                  <FindingCard
                    key={i}
                    finding={bug}
                    type="bug"
                    onJumpToLine={onJumpToLine}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Security */}
        {activeTab === 'security' && (
          <div className="tab-panel animate-fade-in" id="panel-security">
            {security.length === 0 ? (
              <div className="tab-panel__empty">
                <span>✅</span> No security issues found
              </div>
            ) : (
              <div className="findings-list">
                {security.map((sec, i) => (
                  <FindingCard
                    key={i}
                    finding={sec}
                    type="security"
                    onJumpToLine={onJumpToLine}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Complexity */}
        {activeTab === 'complexity' && complexity && (
          <div className="tab-panel animate-fade-in" id="panel-complexity">
            <div className="complexity-overview glass">
              <div className="complexity-metrics">
                <div className="complexity-metric">
                  <span className="complexity-label">Time</span>
                  <span className="complexity-value gradient-text">
                    {complexity.time_complexity}
                  </span>
                </div>
                <div className="complexity-metric">
                  <span className="complexity-label">Space</span>
                  <span className="complexity-value gradient-text">
                    {complexity.space_complexity}
                  </span>
                </div>
              </div>
              <p className="complexity-explanation">{complexity.explanation}</p>
            </div>

            {complexityScores.length > 0 && (
              <div className="complexity-chart-wrapper glass">
                <h4 className="complexity-chart__title">
                  Per-Function Complexity Scores
                </h4>
                <ComplexityChart data={complexityScores} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
