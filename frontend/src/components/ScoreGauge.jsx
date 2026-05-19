/**
 * ScoreGauge.jsx — Animated circular SVG gauge
 *
 * Animates from 0 → overall_score on mount.
 * Color: 80–100 green, 50–79 yellow, 0–49 red.
 *
 * Props:
 *   score — number 0–100
 *   size  — SVG width/height in px (default 140)
 */

import { useState, useEffect, useRef } from 'react';
import './ScoreGauge.css';

function getScoreColor(score) {
  if (score >= 80) return '#22c55e';
  if (score >= 50) return '#f59e0b';
  return '#ef4444';
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent';
  if (score >= 50) return 'Needs Work';
  return 'Critical';
}

export default function ScoreGauge({ score = 0, size = 140 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const rafRef = useRef(null);

  useEffect(() => {
    let start = null;
    const duration = 1200;

    function animate(timestamp) {
      if (!start) start = timestamp;
      const elapsed = timestamp - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * score));

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    }

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [score]);

  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = (animatedScore / 100) * circumference;
  const color = getScoreColor(animatedScore);

  return (
    <div className="score-gauge" id="score-gauge">
      <div className="score-gauge__ring" style={{ width: size, height: size }}>
        <svg viewBox="0 0 120 120" className="score-gauge__svg">
          {/* Background track */}
          <circle
            cx="60" cy="60" r={radius}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="8"
          />
          {/* Animated fill */}
          <circle
            cx="60" cy="60" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${strokeDash} ${circumference}`}
            style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>
        <span className="score-gauge__value" style={{ color }}>
          {animatedScore}
        </span>
      </div>
      <div className="score-gauge__label">
        <span className="score-gauge__title">Overall Score</span>
        <span className="score-gauge__status" style={{ color }}>
          {getScoreLabel(animatedScore)}
        </span>
      </div>
    </div>
  );
}
