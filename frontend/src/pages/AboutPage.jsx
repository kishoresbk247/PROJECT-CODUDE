/**
 * AboutPage.jsx — About CODUDE
 */
import './AboutPage.css';

export default function AboutPage() {
  return (
    <div className="about-page">
      <div className="about-container animate-slide-up">
        <h1 className="about-title">
          About <span className="gradient-text">CODUDE</span>
        </h1>
        <p className="about-lead">
          CODUDE is an AI-powered code review assistant built as a 21-day
          full-stack learning project. It combines a FastAPI backend with a
          React frontend to deliver instant, actionable code feedback.
        </p>

        <div className="about-grid">
          <div className="about-card glass">
            <h3>🎯 Mission</h3>
            <p>Help developers write better, safer, and more efficient code
            by providing instant AI-driven analysis — no waiting for human
            reviewers.</p>
          </div>
          <div className="about-card glass">
            <h3>🛠️ Tech Stack</h3>
            <p><strong>Frontend:</strong> React + Vite + TailwindCSS + CodeMirror<br/>
            <strong>Backend:</strong> FastAPI + Pydantic v2<br/>
            <strong>AI:</strong> LangChain + OpenAI (coming soon)</p>
          </div>
          <div className="about-card glass">
            <h3>📅 21-Day Build</h3>
            <p>This project is being built from scratch over 21 days, with
            each day documented in a detailed log file. Follow along to see
            the entire development journey.</p>
          </div>
          <div className="about-card glass">
            <h3>👤 Developer</h3>
            <p>Built by <strong>Kishore</strong> — learning full-stack development
            by building real projects, one day at a time.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
