/**
 * responseMapper.js — API response → UI shape adapter (Day 18)
 *
 * Why this file exists:
 *   The backend's CodeReviewResponse Pydantic model may evolve independently
 *   of the UI. If the backend renames `bugs` → `bug_findings`, this file is
 *   the ONLY place that needs updating — no UI component needs to change.
 *
 *   This is the Adapter pattern: backend shape in → UI shape out.
 *
 * Backend shape (CodeReviewResponse):
 *   {
 *     overall_score:      number (0–100)
 *     summary:            string
 *     bugs:               BugFinding[]
 *     security:           SecurityFinding[]
 *     complexity:         ComplexityResult | null
 *     processing_time_ms: number
 *     review_id:          string | null
 *   }
 *
 * BugFinding:
 *   { severity, line?, message, suggestion }
 *
 * SecurityFinding:
 *   { severity, line?, message, suggestion, owasp_category? }
 *
 * ComplexityResult:
 *   { time_complexity, space_complexity, explanation, complexity_scores? }
 *   complexity_scores: FunctionComplexity[]
 *   FunctionComplexity: { function_name, time_complexity, space_complexity, score }
 *
 * UI shape (what ResultsTabs / FindingCard / ScoreGauge expect):
 *   Same field names — the backend was designed to match the UI.
 *   We still map explicitly so future divergence is handled here.
 *
 * @typedef {{ severity: string, line?: number, message: string, suggestion?: string }} Finding
 * @typedef {{ severity: string, line?: number, message: string, suggestion?: string, owasp_category?: string }} SecurityFinding
 * @typedef {{ function_name: string, time_complexity: string, space_complexity: string, score: number }} FunctionComplexity
 * @typedef {{ time_complexity: string, space_complexity: string, explanation: string, complexity_scores: FunctionComplexity[] }} Complexity
 * @typedef {{ overall_score: number, summary: string, bugs: Finding[], security: SecurityFinding[], complexity: Complexity|null, processingTimeMs: number, reviewId: string|null }} MappedReviewResponse
 */

/**
 * Map a raw CodeReviewResponse from the API to the shape the UI expects.
 *
 * @param {object} raw — the raw JSON body from the API
 * @returns {MappedReviewResponse}
 */
export function mapReviewResponse(raw) {
  return {
    overall_score: raw.overall_score ?? 0,
    summary:       raw.summary       ?? 'No summary available.',
    bugs:          mapFindings(raw.bugs),
    security:      mapSecurityFindings(raw.security),
    complexity:    mapComplexity(raw.complexity),
    // Additional metadata fields (not used by UI yet, available for future)
    processingTimeMs: raw.processing_time_ms ?? null,
    reviewId:         raw.review_id          ?? null,
  };
}

/**
 * Map an array of BugFinding objects.
 * @param {object[]|null|undefined} items
 * @returns {Finding[]}
 */
function mapFindings(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => ({
    severity:   normalizeSeverity(item.severity),
    line:       item.line ?? null,
    message:    item.message    ?? '',
    suggestion: item.suggestion ?? null,
  }));
}

/**
 * Map an array of SecurityFinding objects.
 * @param {object[]|null|undefined} items
 * @returns {SecurityFinding[]}
 */
function mapSecurityFindings(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => ({
    severity:       normalizeSeverity(item.severity),
    line:           item.line           ?? null,
    message:        item.message        ?? '',
    suggestion:     item.suggestion     ?? null,
    owasp_category: item.owasp_category ?? null,
  }));
}

/**
 * Map ComplexityResult (or null) to the UI complexity shape.
 * @param {object|null|undefined} raw
 * @returns {Complexity|null}
 */
function mapComplexity(raw) {
  if (!raw) return null;

  // Backend uses `complexity_scores` or `visualization.complexity_scores`
  const scores =
    raw.complexity_scores ??
    raw.visualization?.complexity_scores ??
    [];

  return {
    time_complexity:  raw.time_complexity  ?? 'Unknown',
    space_complexity: raw.space_complexity ?? 'Unknown',
    explanation:      raw.explanation      ?? raw.summary ?? '',
    complexity_scores: scores.map((s) => ({
      function_name:    s.function_name    ?? s.name ?? 'anonymous',
      time_complexity:  s.time_complexity  ?? 'O(?)',
      space_complexity: s.space_complexity ?? 'O(?)',
      score:            typeof s.score === 'number' ? s.score : 5,
    })),
  };
}

/**
 * Normalize severity strings to lowercase.
 * Guards against backend sending "Critical" (capitalized) vs "critical".
 * @param {string|undefined} severity
 * @returns {'critical'|'high'|'medium'|'low'}
 */
function normalizeSeverity(severity) {
  const s = (severity ?? 'medium').toLowerCase();
  if (['critical', 'high', 'medium', 'low'].includes(s)) return s;
  return 'medium';
}
