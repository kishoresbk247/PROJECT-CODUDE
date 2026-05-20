/**
 * LoadingSkeleton.jsx — Animated pulse skeleton (Day 17)
 *
 * Shown while useReview.isLoading === true.
 * Mimics the ResultsTabs + FindingCard layout so the page doesn't jump.
 *
 * Design choice: skeleton loaders (vs spinners) because they give the user
 * a sense of the incoming layout, reducing perceived wait time.
 */

import './LoadingSkeleton.css';

/** Single shimmer bar — reusable primitive */
function SkeletonBar({ width = '100%', height = '14px', style = {} }) {
  return (
    <div
      className="skel-bar"
      style={{ width, height, ...style }}
      aria-hidden="true"
    />
  );
}

/** A skeleton that looks like one FindingCard */
function SkeletonFindingCard() {
  return (
    <div className="skel-card glass" aria-hidden="true">
      <div className="skel-card__header">
        <div className="skel-card__badges">
          <SkeletonBar width="64px" height="22px" style={{ borderRadius: '999px' }} />
          <SkeletonBar width="80px" height="22px" style={{ borderRadius: '999px' }} />
        </div>
        <SkeletonBar width="72px" height="22px" style={{ borderRadius: '6px' }} />
      </div>
      <SkeletonBar width="90%" height="14px" style={{ marginTop: '12px' }} />
      <SkeletonBar width="70%" height="14px" style={{ marginTop: '8px' }} />
      <div className="skel-card__suggestion">
        <SkeletonBar width="16px" height="16px" style={{ borderRadius: '4px', flexShrink: 0 }} />
        <SkeletonBar width="85%" height="14px" />
      </div>
    </div>
  );
}

/** Full-panel skeleton mimicking the ResultsTabs layout */
export default function LoadingSkeleton({ cardCount = 3 }) {
  return (
    <div className="skel-wrapper" role="status" aria-label="Loading review results…">
      {/* Tab bar skeleton */}
      <div className="skel-tabs glass">
        {['Overview', 'Bugs', 'Security', 'Complexity'].map((label) => (
          <div key={label} className="skel-tab">
            <SkeletonBar width="18px" height="18px" style={{ borderRadius: '4px' }} />
            <SkeletonBar width={`${label.length * 9}px`} height="14px" />
          </div>
        ))}
      </div>

      {/* Score gauge skeleton */}
      <div className="skel-overview glass">
        <div className="skel-gauge">
          <SkeletonBar width="120px" height="120px" style={{ borderRadius: '50%' }} />
        </div>
        <div className="skel-summary">
          <SkeletonBar width="60%" height="20px" style={{ marginBottom: '12px' }} />
          <SkeletonBar width="100%" height="13px" style={{ marginBottom: '8px' }} />
          <SkeletonBar width="85%"  height="13px" style={{ marginBottom: '8px' }} />
          <SkeletonBar width="75%"  height="13px" />
          <div className="skel-stats">
            {[1, 2, 3].map((n) => (
              <div key={n} className="skel-stat">
                <SkeletonBar width="40px" height="32px" style={{ borderRadius: '8px' }} />
                <SkeletonBar width="50px" height="12px" style={{ marginTop: '6px' }} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Finding cards skeleton */}
      <div className="skel-findings">
        {Array.from({ length: cardCount }).map((_, i) => (
          <SkeletonFindingCard key={i} />
        ))}
      </div>

      <span className="sr-only">Loading review results, please wait…</span>
    </div>
  );
}
