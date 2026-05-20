/**
 * LanguageSelector.jsx — Styled language dropdown (Day 17)
 *
 * Props:
 *   value     {string}    — current language value
 *   onChange  {function}  — (newValue: string) => void
 *
 * Languages: Auto-detect, Python, JavaScript, Java, C++
 * Uses text/emoji icons: 🤖 Auto, 🐍 Python, 🟨 JS, ☕ Java, ➕ C++
 */

import './LanguageSelector.css';

export const LANGUAGES = [
  { value: 'auto',       label: 'Auto-detect', icon: '🤖' },
  { value: 'python',     label: 'Python',       icon: '🐍' },
  { value: 'javascript', label: 'JavaScript',   icon: '🟨' },
  { value: 'java',       label: 'Java',         icon: '☕' },
  { value: 'cpp',        label: 'C++',          icon: '➕' },
];

export default function LanguageSelector({ value, onChange }) {
  const selected = LANGUAGES.find((l) => l.value === value) || LANGUAGES[0];

  return (
    <div className="lang-selector" id="language-selector-wrapper">
      {/* Visual preview of selected icon */}
      <span className="lang-selector__icon" aria-hidden="true">
        {selected.icon}
      </span>

      <select
        id="language-selector"
        className="lang-selector__select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Select programming language"
      >
        {LANGUAGES.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.icon} {lang.label}
          </option>
        ))}
      </select>

      {/* Custom chevron */}
      <svg
        className="lang-selector__chevron"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </div>
  );
}
