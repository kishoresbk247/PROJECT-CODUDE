"""
CoDude — Review Service (Day 07 — Static Analysis Layer)

Orchestrates both static analysis and AI-powered review:

    Static Analysis (Python only — no API call):
        1. ASTAnalyzer       — mutable defaults, bare excepts, None comparison, unused vars
        2. ComplexityChecker  — cyclomatic complexity > 10
        3. StyleChecker       — snake_case, function length, docstrings

    LLM Analysis (all languages):
        1. Bug Detection     — BUG_DETECTION_PROMPT | llm(BugDetectionSchema)
        2. Security Review   — SECURITY_REVIEW_PROMPT | llm(SecurityReviewSchema)
        3. Complexity Analysis — COMPLEXITY_ANALYSIS_PROMPT | llm(ComplexityAnalysisSchema)

Day 07 additions over Day 06:
    - AST-based static analysis runs BEFORE the LLM call (Python only)
    - Static findings are tagged with source="static"
    - LLM findings are tagged with source="llm"
    - Both are merged into the final response
    - Language guard: non-Python code skips static analysis entirely

Architecture:
    Static analysis is synchronous and instant (< 10ms).
    LLM chains are async and run concurrently via asyncio.gather().
    Static findings appear first in the bugs list.
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
from app.services.static_analysis import ASTAnalyzer, ComplexityChecker, StyleChecker

logger = logging.getLogger(__name__)


class ReviewService:
    """
    High-level service for AI-powered code reviews.

    Day 07: Adds AST-based static analysis before the LLM call.
    Python code gets instant static findings + LLM findings.
    Non-Python code gets LLM-only analysis.

    Usage:
        service = ReviewService()
        response = await service.review(request)
    """

    def __init__(self) -> None:
        """Initialise the LLM service, cache service, static analyzers, and LCEL chains."""
        self._llm_service = LLMService()
        self._cache = CacheService()

        # ── Static Analyzers (Python only, no API call) ──────────────────
        self._ast_analyzer = ASTAnalyzer()
        self._complexity_checker = ComplexityChecker()
        self._style_checker = StyleChecker()

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
        Run a full code review with static analysis + LLM + Redis caching.

        Flow:
            1. Generate cache key from sha256(code + language)
            2. Check Redis for a cached response
            3. On HIT → deserialise and return immediately
            4. On MISS →
               a. Run static analysis (Python only, instant)
               b. Run all three LLM chains in parallel
               c. Merge static + LLM results, cache, return

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

        # ── Step 3: Cache MISS — run analysis ────────────────────────────
        logger.info(
            "❌ Cache MISS — running review — language=%s, code_length=%d",
            request.language,
            len(request.code),
        )

        # ── Step 3a: Static Analysis (Python only) ───────────────────────
        static_bugs = self._run_static_analysis(request.code, request.language)
        if static_bugs:
            logger.info(
                "🔍 Static analysis found %d issue(s) — source=static",
                len(static_bugs),
            )

        # ── Step 3b: LLM Analysis (all languages) ───────────────────────
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
        response = self._merge_results(
            bug_result, security_result, complexity_result, static_bugs
        )

        # ── Step 5: Cache the response ───────────────────────────────────
        await self._cache.set(cache_key, response.model_dump(), ttl=3600)
        logger.info("📦 Cached review response — TTL=3600s")

        return response

    def _run_static_analysis(self, code: str, language: str) -> list[BugFinding]:
        """
        Run all static analyzers on Python code.

        Language guard: returns an empty list for non-Python code,
        falling through to LLM-only analysis.

        Args:
            code: The source code to analyze.
            language: Programming language of the code.

        Returns:
            List of BugFinding objects with source="static".
        """
        if language.lower() != "python":
            logger.debug("Skipping static analysis — language=%s (not Python)", language)
            return []

        findings: list[BugFinding] = []

        # Run all three analyzers
        for analyzer_finding in (
            self._ast_analyzer.analyze(code)
            + self._complexity_checker.analyze(code)
            + self._style_checker.analyze(code)
        ):
            findings.append(
                BugFinding(
                    line=analyzer_finding.line,
                    severity=analyzer_finding.severity,
                    message=analyzer_finding.message,
                    suggestion=analyzer_finding.suggestion,
                    source="static",
                )
            )

        return findings

    @staticmethod
    def _merge_results(
        bug_result: BugDetectionSchema,
        security_result: SecurityReviewSchema,
        complexity_result: ComplexityAnalysisSchema,
        static_bugs: list[BugFinding] | None = None,
    ) -> CodeReviewResponse:
        """
        Merge outputs from static analysis and three LLM chains into a single response.

        Static findings appear first (source="static"), followed by LLM findings
        (source="llm"). This ordering reflects their detection priority.
        """
        # Map LLM schemas to API response models (tagged source="llm")
        llm_bugs = [
            BugFinding(
                line=b.line,
                severity=b.severity,
                message=b.message,
                suggestion=b.suggestion,
                source="llm",
            )
            for b in bug_result.bugs
        ]

        # Combine static + LLM bugs (static first)
        all_bugs = (static_bugs or []) + llm_bugs

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
        score = ReviewService._compute_score(all_bugs, security)

        # Synthesise summary from findings
        summary = ReviewService._synthesise_summary(all_bugs, security, complexity)

        return CodeReviewResponse(
            bugs=all_bugs,
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

        # Bug summary (broken down by source)
        if bugs:
            static_count = sum(1 for b in bugs if b.source == "static")
            llm_count = sum(1 for b in bugs if b.source == "llm")
            critical_bugs = sum(1 for b in bugs if b.severity == "critical")
            high_bugs = sum(1 for b in bugs if b.severity == "high")

            source_detail = []
            if static_count:
                source_detail.append(f"{static_count} static")
            if llm_count:
                source_detail.append(f"{llm_count} AI")

            parts.append(
                f"Found {len(bugs)} bug(s)"
                + (f" ({', '.join(source_detail)})" if source_detail else "")
                + (f" — {critical_bugs} critical, {high_bugs} high" if critical_bugs or high_bugs else "")
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
