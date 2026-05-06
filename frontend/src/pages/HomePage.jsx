/**
 * HomePage.jsx — Landing Page
 *
 * Explains what CODUDE does with a hero section, feature cards,
 * and a call-to-action button that navigates to /review.
 */

import { useNavigate } from 'react-router-dom';
import './HomePage.css';

const FEATURES = [
  {
    icon: '🐛',
    title: 'Bug Detection',
    description:
      'AI scans your code for common bugs, logic errors, and potential runtime exceptions before they reach production.',
  },
  {
    icon: '🔒',
    title: 'Security Audit',
    description:
      'Identifies vulnerabilities mapped to OWASP categories — SQL injection, XSS, insecure dependencies, and more.',
  },
  {
    icon: '⚡',
    title: 'Complexity Analysis',
    description:
      'Get Big-O time & space complexity for your algorithms, with suggestions for more efficient alternatives.',
  },
  {
    icon: '📊',
    title: 'Quality Score',
    description:
      'Receive an overall code quality score (0–100) with a detailed breakdown to track your improvement over time.',
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      {/* ── Hero Section ── */}
      <section className="hero" id="hero-section">
        <div className="hero-content animate-slide-up">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            AI-Powered Code Review
          </div>

          <h1 className="hero-title">
            Write Better Code with{' '}
            <span className="gradient-text">CODUDE</span>
          </h1>

          <p className="hero-subtitle">
            Your AI pair programmer that catches bugs, flags security issues,
            and analyses algorithm complexity — all in seconds.
          </p>

          <div className="hero-actions">
            <button
              className="btn btn-primary"
              onClick={() => navigate('/review')}
              id="hero-cta-button"
            >
              <span>Start Reviewing</span>
              <span className="btn-arrow">→</span>
            </button>
            <button
              className="btn btn-secondary"
              onClick={() =>
                document
                  .getElementById('features-section')
                  ?.scrollIntoView({ behavior: 'smooth' })
              }
              id="hero-learn-more"
            >
              Learn More
            </button>
          </div>

          {/* Stats */}
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value gradient-text">4</span>
              <span className="hero-stat-label">Analysis Types</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value gradient-text">5+</span>
              <span className="hero-stat-label">Languages</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value gradient-text">&lt;5s</span>
              <span className="hero-stat-label">Response Time</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section className="features" id="features-section">
        <h2 className="features-heading">
          Everything you need to{' '}
          <span className="gradient-text">ship with confidence</span>
        </h2>

        <div className="features-grid">
          {FEATURES.map((feature, index) => (
            <div
              key={feature.title}
              className="feature-card glass"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Section ── */}
      <section className="cta-section" id="cta-section">
        <div className="cta-card glass glow-border">
          <h2 className="cta-title">Ready to level up your code?</h2>
          <p className="cta-subtitle">
            Paste your code, pick a language, and get instant AI-powered feedback.
          </p>
          <button
            className="btn btn-primary btn-lg"
            onClick={() => navigate('/review')}
            id="cta-review-button"
          >
            Go to Code Review →
          </button>
        </div>
      </section>
    </div>
  );
}
