/**
 * reviewApi.js — Review API functions (Day 18)
 *
 * Thin wrapper around the axios client for review-related endpoints.
 * All functions accept an optional AbortController signal so callers
 * can cancel in-flight requests.
 *
 * Exports:
 *   submitReview(payload, signal) — POST /api/v1/review
 *   getHealthCheck(signal)        — GET /health
 */

import apiClient from './client';
import { mapReviewResponse } from './responseMapper';

/**
 * Submit a code review request to the backend pipeline.
 *
 * @param {{ code: string, language: string }} payload
 * @param {AbortSignal} [signal] — from AbortController, cancels the request
 * @returns {Promise<import('./responseMapper').MappedReviewResponse>}
 */
export async function submitReview(payload, signal) {
  const response = await apiClient.post('/api/v1/review', payload, { signal });
  // Map the raw backend shape → UI shape before returning
  return mapReviewResponse(response.data);
}

/**
 * Health check — verify the backend is reachable.
 *
 * @param {AbortSignal} [signal]
 * @returns {Promise<{ status: string, service: string }>}
 */
export async function getHealthCheck(signal) {
  const response = await apiClient.get('/health', { signal });
  return response.data;
}
