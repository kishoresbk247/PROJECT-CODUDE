/**
 * client.js — Configured Axios instance (Day 18)
 *
 * Sets up a shared axios instance with:
 *   1. baseURL from VITE_API_BASE_URL env var (default: http://localhost:8000)
 *   2. Request interceptor — attaches X-Request-ID header (crypto.randomUUID)
 *   3. Response interceptor — normalises all API errors into:
 *        { message: string, statusCode: number, requestId: string }
 *
 * Every other module (reviewApi, etc.) imports this instance — never raw axios.
 * This means request/response transformations are applied globally in one place.
 */

import axios from 'axios';

// ── Create the instance ──────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120_000, // 2 minutes — LLM calls can be slow
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// ── Request interceptor: attach X-Request-ID ────────────────────────────────

apiClient.interceptors.request.use(
  (config) => {
    // crypto.randomUUID() is available in all modern browsers and Node 14.17+
    const requestId =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `req-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    config.headers['X-Request-ID'] = requestId;

    // Attach to config so the response interceptor can read it
    config.metadata = { requestId, startTime: Date.now() };

    if (import.meta.env.DEV) {
      console.debug(`[API] → ${config.method?.toUpperCase()} ${config.url}`, {
        requestId,
        data: config.data,
      });
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor: normalise errors ───────────────────────────────────

apiClient.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      const elapsed = Date.now() - (response.config.metadata?.startTime ?? 0);
      console.debug(
        `[API] ← ${response.status} ${response.config.url} (${elapsed}ms)`,
      );
    }
    return response;
  },
  (error) => {
    // Build a consistent error object regardless of error type
    const requestId = error.config?.metadata?.requestId ?? 'unknown';
    const statusCode = error.response?.status ?? 0;

    let message = 'An unexpected error occurred. Please try again.';

    if (error.code === 'ERR_CANCELED' || error.name === 'CanceledError') {
      // Request was aborted intentionally — don't treat as an error
      message = 'Request cancelled.';
    } else if (error.response) {
      // Server responded with a non-2xx status
      const data = error.response.data;
      message =
        data?.detail ||
        data?.message ||
        data?.error_message ||
        `Server error (${statusCode})`;
    } else if (error.request) {
      // Request was made but no response received (network error / timeout)
      message =
        error.code === 'ECONNABORTED'
          ? 'Request timed out — the AI service is taking too long. Try again.'
          : 'Cannot reach the server. Is the backend running?';
    }

    // Attach normalized shape to the error so callers can destructure cleanly
    error.normalized = { message, statusCode, requestId };

    if (import.meta.env.DEV && error.code !== 'ERR_CANCELED') {
      console.error('[API] Error', { message, statusCode, requestId });
    }

    return Promise.reject(error);
  },
);

export default apiClient;
