/**
 * SeverityBadge.jsx — Severity indicator pill
 *
 * Renders a small colour-coded badge based on the severity level.
 * Uses Tailwind CSS utility classes for styling.
 *
 * Colour mapping:
 *   critical → red
 *   high     → orange
 *   medium   → yellow
 *   low      → blue
 */

const SEVERITY_STYLES = {
  critical:
    'bg-red-500/15 text-red-400 border border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.15)]',
  high:
    'bg-orange-500/15 text-orange-400 border border-orange-500/30 shadow-[0_0_8px_rgba(249,115,22,0.15)]',
  medium:
    'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 shadow-[0_0_8px_rgba(245,158,11,0.15)]',
  low:
    'bg-blue-500/15 text-blue-400 border border-blue-500/30 shadow-[0_0_8px_rgba(59,130,246,0.15)]',
};

export default function SeverityBadge({ severity }) {
  const tw = SEVERITY_STYLES[severity] || SEVERITY_STYLES.low;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider leading-tight ${tw}`}
      id={`severity-badge-${severity}`}
    >
      {severity}
    </span>
  );
}
