/**
 * Layout.jsx — Main Layout Component
 *
 * Wraps all pages with a consistent navbar and footer.
 * Uses react-router-dom's <Outlet /> to render child routes.
 * The navbar features the "CODUDE" brand with gradient text,
 * glassmorphism styling, and smooth hover animations.
 */

import { NavLink, Outlet } from 'react-router-dom';
import './Layout.css';

export default function Layout() {
  return (
    <div className="layout">
      {/* ── Background Ambient Glow ── */}
      <div className="ambient-glow" aria-hidden="true" />

      {/* ── Navbar ── */}
      <nav className="navbar glass" id="main-navbar">
        <div className="navbar-inner">
          {/* Brand */}
          <NavLink to="/" className="brand" id="brand-link">
            <span className="brand-icon">⚡</span>
            <span className="brand-text gradient-text">CODUDE</span>
          </NavLink>

          {/* Navigation Links */}
          <div className="nav-links">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
              id="nav-home"
            >
              Home
            </NavLink>
            <NavLink
              to="/review"
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
              id="nav-review"
            >
              Review
            </NavLink>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
              id="nav-about"
            >
              About
            </NavLink>
          </div>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="main-content animate-fade-in">
        <Outlet />
      </main>

      {/* ── Footer ── */}
      <footer className="footer" id="main-footer">
        <p className="footer-text">
          Built with <span className="footer-heart">♥</span> by Kishore
          <span className="footer-separator">·</span>
          <span className="gradient-text">CODUDE</span> — AI Code Review Assistant
        </p>
      </footer>
    </div>
  );
}
