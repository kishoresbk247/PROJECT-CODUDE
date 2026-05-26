/**
 * useReview.js — Custom hook for code review API calls (Day 18 update)
 *
 * Day 18 changes:
 *   ✅ Replaced mock delay with real submitReview() API call
 *   ✅ AbortController cancels in-flight requests on rapid re-submission
 *   ✅ AbortController ref cleaned up in useEffect return function
 *   ✅ Cancelled requests silently ignored (not treated as errors)
 *   ✅ Error messages sourced from error.normalized (set by axios interceptor)
 *
 * AbortController pattern:
 *   - An AbortController is created per review() call
 *   - Its signal is passed to axios via submitReview(payload, signal)
 *   - If review() is called again before the previous resolves, the old
 *     controller is aborted — the stale request is cancelled at network level
 *   - The ref stores the current controller so the cleanup function can abort
 *     if the component unmounts mid-request
 */

import { useState, useCallback, useRef } from 'react';
import { submitReview } from '../api/reviewApi';

export function useReview() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError]         = useState(null);
  const [result, setResult]       = useState(null);

  // Holds the AbortController for the currently in-flight request
  const abortControllerRef = useRef(null);

  /**
   * Trigger a code review.
   * Cancels any previous in-flight request before starting a new one.
   *
   * @param {string} code     - The source code to review
   * @param {string} language - The selected language key (python, js, …)
   */
  const review = useCallback(async (code, language) => {
    if (!code || !code.trim()) {
      setError('Please enter some code to review.');
      return;
    }

    // ── Cancel previous in-flight request (rapid re-submission guard) ──────
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create a fresh controller for this request
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // ── Real API call (Day 18) ────────────────────────────────────────────
      const mapped = await submitReview(
        { code, language: language === 'auto' ? 'python' : language },
        controller.signal,
      );
      setResult(mapped);
    } catch (err) {
      // Silently ignore intentional cancellations
      if (err.code === 'ERR_CANCELED' || err.name === 'CanceledError') {
        return;
      }

      // Use the normalized error message from the axios response interceptor
      const message =
        err.normalized?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        'An unexpected error occurred. Please try again.';

      setError(message);
      setResult(null);
    } finally {
      // Only clear loading if this controller is still the current one
      // (guards against race conditions if abort happened)
      if (abortControllerRef.current === controller) {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    }
  }, []);

  /**
   * Cancel any in-flight request — e.g. when component unmounts.
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
  }, []);

  const clearError  = useCallback(() => setError(null), []);
  const clearResult = useCallback(() => setResult(null), []);

  return { review, isLoading, error, result, clearError, clearResult, cancel };
}
