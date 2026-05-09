"""
CoDude — Review Service (Day 06 — Caching Layer)

Orchestrates three parallel AI review chains using asyncio.gather():

    1. Bug Detection     — BUG_DETECTION_PROMPT | llm(BugDetectionSchema)
    2. Security Review   — SECURITY_REVIEW_PROMPT | llm(SecurityReviewSchema)
    3. Complexity Analysis — COMPLEXITY_ANALYSIS_PROMPT | llm(ComplexityAnalysisSchema)

Day 06 additions over Day 05:
    - Redis-based response caching via CacheService
    - Cache key = sha256(code + language) for deduplication
    - Cache HIT → return instantly (skip all three LLM chains)
    - Cache MISS → run chains, store result, return
    - Logging of cache hit/miss for observability

Architecture:
    Each chain is an LCEL pipeline: prompt | llm.with_structured_output(schema)
    All three chains run concurrently, and results are merged into a single
    CodeReviewResponse with a synthesized summary and score.
"""

import asyncio
import logging

from app.models.review import (
    BugFinding,
    CodeReviewRequest,
    CodeReviewResponse,
    ComplexityResult,
    SecurityFinding,
)
from app.services.cache_service import CacheService
from app.services.llm_service import LLMService
from app.services.prompts.bug_detection import BUG_DETECTION_PROMPT
from app.services.prompts.complexity_analysis import COMPLEXITY_ANALYSIS_PROMPT
from app.services.prompts.security_review import SECURITY_REVIEW_PROMPT
from app.services.prompts.structured_output import (
    BugDetectionSchema,
    ComplexityAnalysisSchema,
    SecurityReviewSchema,
)

logger = logging.getLogger(__name__)


class ReviewService:
    """
    High-level service for AI-powered code reviews.

    Day 06: Adds Redis caching around the parallel LLM chains.
    On a cache hit, the LLM is never called — instant response.

    Usage:
        service = ReviewService()
        response = await service.review(request)
    """

    def __init__(self) -> None:
        """Initialise the LLM service, cache service, and LCEL chains."""
        self._llm_service = LLMService()
        self._cache = CacheService()

        # ── Specialized LCEL Chains ──────────────────────────────────────
        # Each chain: prompt | llm_with_structured_output(schema)
        # Nothing executes until .ainvoke() is called (lazy evaluation).

        self._bug_chain = (
            BUG_DETECTION_PROMPT
            | self._llm_service.with_structured_output(BugDetectionSchema)
        )

        self._security_chain = (
            SECURITY_REVIEW_PROMPT
            | self._llm_service.with_structured_output(SecurityReviewSchema)
        )

        self._complexity_chain = (
            COMPLEXITY_ANALYSIS_PROMPT
            | self._llm_service.with_structured_output(ComplexityAnalysisSchema)
        )

    async def review(self, request: CodeReviewRequest) -> CodeReviewResponse:
        """
        Run a full AI code review with Redis caching.

        Flow:
            1. Generate cache key from sha256(code + language)
            2. Check Redis for a cached response
            3. On HIT → deserialise and return immediately
            4. On MISS → run all three LLM chains in parallel
            5. Merge results, cache the response, return

        Args:
            request: The client's code review request containing
                     code, language, and optional filename.

        Returns:
            A CodeReviewResponse with bugs, security findings,
            complexity analysis, summary, and overall score.
        """
        # ── Step 1: Build cache key ──────────────────────────────────────
        cache_key = CacheService.make_key(request.code, request.language)

        # ── Step 2: Check cache ──────────────────────────────────────────
        cached_data = await self._cache.get(cache_key)
        if cached_data is not None:
            logger.info("✅ Cache HIT — returning cached review")
            return CodeReviewResponse(**cached_data)

        # ── Step 3: Cache MISS — run LLM chains ─────────────────────────
        logger.info(
            "❌ Cache MISS — running parallel LLM review — language=%s, code_length=%d",
            request.language,
            len(request.code),
        )

        chain_input = {
            "language": request.language,
            "code": request.code,
        }

        # Run all three chains in parallel
        bug_result, security_result, complexity_result = await asyncio.gather(
            self._bug_chain.ainvoke(chain_input),
            self._security_chain.ainvoke(chain_input),
            self._complexity_chain.ainvoke(chain_input),
        )

        logger.info(
            "All chains complete — bugs=%d, security=%d",
            len(bug_result.bugs),
            len(security_result.security),
        )

        # ── Step 4: Merge results ────────────────────────────────────────
        response = self._merge_results(bug_result, security_result, complexity_result)

        # ── Step 5: Cache the response ───────────────────────────────────
        await self._cache.set(cache_key, response.model_dump(), ttl=3600)
        logger.info("📦 Cached review response — TTL=3600s")

        return response

    @staticmethod
    def _merge_results(
        bug_result: BugDetectionSchema,
        security_result: SecurityReviewSchema,
        complexity_result: ComplexityAnalysisSchema,
    ) -> CodeReviewResponse:
        """
        Merge outputs from three specialized chains into a single response.

        Synthesises a summary and computes an overall score based on the
        number and severity of findings.
        """
        # Map LLM schemas to API response models
        bugs = [
            BugFinding(
                line=b.line,
                severity=b.severity,
                message=b.message,
                suggestion=b.suggestion,
            )
            for b in bug_result.bugs
        ]

        security = [
            SecurityFinding(
                line=s.line,
                severity=s.severity,
                message=s.message,
                suggestion=s.suggestion,
                owasp_category=s.owasp_category,
            )
            for s in security_result.security
        ]

        complexity = ComplexityResult(
            time_complexity=complexity_result.time_complexity,
            space_complexity=complexity_result.space_complexity,
            explanation=complexity_result.explanation,
            brute_force_alternative=complexity_result.suggestion,
        )

        # Compute overall score based on findings
        score = ReviewService._compute_score(bugs, security)

        # Synthesise summary from findings
        summary = ReviewService._synthesise_summary(bugs, security, complexity)

        return CodeReviewResponse(
            bugs=bugs,
            security=security,
            complexity=complexity,
            summary=summary,
            overall_score=score,
        )

    @staticmethod
    def _compute_score(
        bugs: list[BugFinding],
        security: list[SecurityFinding],
    ) -> int:
        """
        Compute a quality score from 0–100 based on findings.

        Scoring logic:
            - Start at 100
            - Each critical finding: -20
            - Each high finding: -15
            - Each medium finding: -8
            - Each low finding: -3
            - Minimum score is 0
        """
        severity_penalties = {
            "critical": 20,
            "high": 15,
            "medium": 8,
            "low": 3,
        }

        score = 100
        for finding in [*bugs, *security]:
            score -= severity_penalties.get(finding.severity, 5)

        return max(0, score)

    @staticmethod
    def _synthesise_summary(
        bugs: list[BugFinding],
        security: list[SecurityFinding],
        complexity: ComplexityResult,
    ) -> str:
        """
        Generate a human-readable summary from the parallel chain results.
        """
        parts = []

        # Bug summary
        if bugs:
            critical_bugs = sum(1 for b in bugs if b.severity == "critical")
            high_bugs = sum(1 for b in bugs if b.severity == "high")
            parts.append(
                f"Found {len(bugs)} bug(s)"
                + (f" ({critical_bugs} critical, {high_bugs} high)" if critical_bugs or high_bugs else "")
                + "."
            )
        else:
            parts.append("No bugs detected.")

        # Security summary
        if security:
            critical_sec = sum(1 for s in security if s.severity == "critical")
            categories = set(s.owasp_category for s in security)
            parts.append(
                f"Found {len(security)} security issue(s)"
                + (f" ({critical_sec} critical)" if critical_sec else "")
                + f" across {len(categories)} OWASP category(ies)."
            )
        else:
            parts.append("No security vulnerabilities found.")

        # Complexity summary
        parts.append(
            f"Complexity: {complexity.time_complexity} time, "
            f"{complexity.space_complexity} space."
        )
        if complexity.brute_force_alternative:
            parts.append("An optimised alternative was suggested.")

        return " ".join(parts)
