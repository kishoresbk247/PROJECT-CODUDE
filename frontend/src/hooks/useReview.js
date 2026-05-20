/**
 * useReview.js — Custom hook for code review API calls (Day 17)
 *
 * Encapsulates:
 *   - isLoading state
 *   - error state
 *   - result state
 *   - review() trigger function
 *
 * Any component that needs to trigger a review just calls:
 *   const { review, isLoading, error, result, clearError } = useReview();
 *
 * Day 18 will swap the mock delay for a real axios POST to /api/review.
 */

import { useState, useCallback } from 'react';
import MOCK_REVIEW_RESPONSE from '../data/mockReviewData';

// Artificial delay (ms) to showcase loading skeleton — remove on Day 18
const MOCK_DELAY_MS = 2000;

export function useReview() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState(null);
  const [result, setResult]       = useState(null);

  /**
   * Trigger a code review.
   * @param {string} code     - The source code string to review
   * @param {string} language - The selected language key (python, javascript, …)
   */
  const review = useCallback(async (code, language) => {
    if (!code || !code.trim()) {
      setError('Please enter some code to review.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // ── Day 18: replace this block with real axios call ──────────────────
      // const response = await axios.post('/api/review', { code, language });
      // setResult(response.data);
      // ─────────────────────────────────────────────────────────────────────

      // Artificial 2-second delay to demo skeleton loaders
      await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));

      // Simulate an occasional random error (10% chance) — remove on Day 18
      // if (Math.random() < 0.1) throw new Error('Mock API timeout');

      setResult(MOCK_REVIEW_RESPONSE);
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'An unexpected error occurred. Please try again.';
      setError(message);
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  const clearResult = useCallback(() => setResult(null), []);

  return { review, isLoading, error, result, clearError, clearResult };
}
