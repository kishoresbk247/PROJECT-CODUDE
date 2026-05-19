"""
CoDude — Review Pipeline (Day 15 — Visualization Data & Narrative Summary)

Fan-out, fan-in architecture that unifies all bug detection sources
(AST + regex + LLM) into a single pipeline with:

    1. Deduplication  — removes duplicate findings across sources
    2. Priority sort  — critical > high > medium > low, then by line
    3. Scoring        — computed overall_score with security 1.5× weight

Day 12 additions:
    - OWASP static scanner integrated (runs alongside LLM security chain)
    - ExploitExplainer enriches critical/high findings
    - asyncio.gather() runs all exploit explanations in parallel
    - In-memory review store for security-report endpoint

Day 13 additions:
    - Per-function complexity annotator (ASTComplexityAnalyzer + SpaceAnalyzer)
    - ComplexityService runs AST first, LLM fallback for low-confidence
    - FunctionComplexity objects attached to ComplexityResult

Day 14 additions:
    - BruteForceDetector identifies suboptimal algorithm patterns
    - SolutionGenerator produces targeted LLM-powered optimisations
    - OptimizationOpportunity objects attached to ComplexityResult

Day 15 additions:
    - ComplexityVisualizer converts analysis to frontend-ready chart data
    - SummaryGenerator produces LLM-powered executive narrative summaries
    - ComplexityVisualization + summary attached to ComplexityResult

Pipeline order:
    ┌─────────────────────────────────────────────────────────────────┐
    │ 1. Language Detection  (sync, <1ms)                            │
    │ 2. AST Analysis        (sync, Python only, <10ms)              │
    │ 3. Regex Matching      (sync, JS/Java, <10ms)                  │
    │ 4. OWASP Static Scan   (sync, all languages, <1ms)             │
    │ 5. Per-Function Complexity (sync AST + async LLM, <10ms+)      │
    │ 6. LLM Calls           (async, all languages, ~1.5s parallel)  │
    │    ├─ Bug Detection                                            │
    │    ├─ Security Review                                          │
    │    └─ Complexity Analysis (overall)                             │
    │ 7. Merge Security (LLM + OWASP static)                        │
    │ 8. Exploit Enrichment  (async, critical/high only, parallel)   │
    │ 9. Merge + Deduplicate + Sort + Score                          │
    └─────────────────────────────────────────────────────────────────┘

The asyncio.gather() call runs all three LLM chains concurrently,
reducing total latency from ~(t₁+t₂+t₃) to ~max(t₁,t₂,t₃).
At typical GPT-4o-mini speeds (~1.5s/call), this yields a 3× speedup.

Usage:
    pipeline = ReviewPipeline()
    response = await pipeline.run(request)
"""

import asyncio
import logging
import time
from difflib import SequenceMatcher

from app.models.review import (
    BugFinding,
    CodeReviewRequest,
    CodeReviewResponse,
    ComplexityResult,
    FunctionComplexity,
    OptimizationOpportunity,
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
from app.services.complexity import ComplexityService, ComplexityVisualizer
from app.services.complexity.summary_generator import generate_summary
from app.services.security.exploit_explainer import ExploitExplainer
from app.services.security.owasp_scanner import OWASPScanner
from app.services.static_analysis import (
    ASTAnalyzer,
    ComplexityChecker,
    LanguageDetector,
    PatternMatcher,
    StyleChecker,
)

logger = logging.getLogger(__name__)

# ── Severity ordering (lower index = higher priority) ────────────────────────
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# ── Score penalty weights per severity ───────────────────────────────────────
_BUG_PENALTIES = {"critical": 25, "high": 15, "medium": 7, "low": 2}

# Security findings count 1.5× their bug-equivalent penalty
_SECURITY_MULTIPLIER = 1.5

# Message similarity threshold for deduplication (80%)
_SIMILARITY_THRESHOLD = 0.80

# ── In-memory review store (Day 12) ──────────────────────────────────────────
# Maps review_id → CodeReviewResponse for the security-report endpoint.
# Will be replaced by persistent storage in Day 19.
_review_store: dict[str, "CodeReviewResponse"] = {}


class ReviewPipeline:
    """
    Unified bug detection pipeline that merges static analysis and LLM
    findings into a single, deduplicated, priority-sorted response.

    Usage:
        pipeline = ReviewPipeline()
        response = await pipeline.run(request)
    """

    def __init__(self) -> None:
        """Initialise all analyzers, LLM chains, cache, and language detector."""
        self._llm_service = LLMService()
        self._cache = CacheService()
        self._language_detector = LanguageDetector()

        # ── Static Analyzers ─────────────────────────────────────────────
        self._ast_analyzer = ASTAnalyzer()
        self._complexity_checker = ComplexityChecker()
        self._style_checker = StyleChecker()
        self._pattern_matcher = PatternMatcher()

        # ── OWASP Scanner + Exploit Explainer (Day 12) ───────────────────
        self._owasp_scanner = OWASPScanner()
        self._exploit_explainer = ExploitExplainer()

        # ── Per-Function Complexity Annotator (Day 13) ───────────────────
        self._complexity_service = ComplexityService()

        # ── LCEL Chains (lazy — nothing runs until .ainvoke()) ───────────
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

        # ── Review counter for generating IDs ────────────────────────────
        self._review_counter = 0

    async def run(self, request: CodeReviewRequest) -> CodeReviewResponse:
        """
        Execute the full review pipeline.

        Steps:
            1. Auto-detect language (if "auto")
            2. Check cache
            3. Run static analysis (sync)
            4. Run LLM chains in parallel (async)
            5. Merge, deduplicate, sort, score
            6. Cache result
            7. Return response with processing_time_ms

        Args:
            request: The client's code review request.

        Returns:
            A fully populated CodeReviewResponse.
        """
        t_start = time.perf_counter()

        # ── Step 1: Language Detection ───────────────────────────────────
        if request.language.lower() == "auto":
            detected = self._language_detector.detect(
                code=request.code, filename=request.filename
            )
            logger.info(
                "Pipeline: auto-detected language → %s (filename=%s)",
                detected,
                request.filename,
            )
            request = request.model_copy(update={"language": detected})

        # ── Step 2: Cache Check ──────────────────────────────────────────
        cache_key = CacheService.make_key(request.code, request.language)
        cached_data = await self._cache.get(cache_key)
        if cached_data is not None:
            logger.info("Pipeline: cache HIT — returning cached review")
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            cached_data["processing_time_ms"] = elapsed_ms
            return CodeReviewResponse(**cached_data)

        logger.info(
            "Pipeline: cache MISS — running full pipeline — lang=%s, len=%d",
            request.language,
            len(request.code),
        )

        # ── Step 3: Static Analysis (sync, <10ms) ───────────────────────
        static_bugs = self._run_static_analysis(request.code, request.language)
        if static_bugs:
            logger.info(
                "Pipeline: static analysis found %d issue(s)", len(static_bugs)
            )

        # ── Step 4: OWASP Static Security Scan (sync, <1ms) ─────────────
        owasp_findings = self._owasp_scanner.scan(
            request.code, language=request.language
        )
        if owasp_findings:
            logger.info(
                "Pipeline: OWASP scanner found %d issue(s)", len(owasp_findings)
            )

        # ── Step 5: LLM Analysis (async, parallel) ──────────────────────
        chain_input = {"language": request.language, "code": request.code}

        bug_result, security_result, complexity_result = await asyncio.gather(
            self._bug_chain.ainvoke(chain_input),
            self._security_chain.ainvoke(chain_input),
            self._complexity_chain.ainvoke(chain_input),
        )

        logger.info(
            "Pipeline: LLM complete — bugs=%d, security=%d",
            len(bug_result.bugs),
            len(security_result.security),
        )

        # ── Step 6: Merge + Deduplicate + Sort + Score ───────────────────
        # Convert LLM bug schemas → API BugFinding models (source="llm")
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

        all_bugs = (static_bugs or []) + llm_bugs
        all_bugs = self._deduplicate_findings(all_bugs)
        all_bugs = self._sort_findings(all_bugs)

        # Convert LLM security schemas → API SecurityFinding models
        llm_security = [
            SecurityFinding(
                line=s.line,
                severity=s.severity,
                message=s.message,
                suggestion=s.suggestion,
                owasp_category=s.owasp_category,
            )
            for s in security_result.security
        ]

        # Convert OWASP static findings → API SecurityFinding models
        owasp_security = [
            SecurityFinding(
                line=f.line,
                severity=f.severity,
                message=f.message,
                suggestion=f.suggestion,
                owasp_category=f.owasp_category,
                cwe_id=f.cwe_id,
                references=[f.remediation_link] if f.remediation_link else [],
            )
            for f in owasp_findings
        ]

        # Merge LLM + OWASP security findings
        security = llm_security + owasp_security

        # ── Step 7: Exploit Enrichment (async, critical/high only) ───────
        security = await self._enrich_security_findings(
            security, request.code, request.language
        )

        # ── Step 7b: Per-Function Complexity + Brute-Force Detection (Day 14) ─
        function_complexities, optimization_opportunities = (
            await self._complexity_service.analyze(
                request.code, request.language
            )
        )
        if function_complexities:
            logger.info(
                "Pipeline: per-function complexity — %d function(s) annotated",
                len(function_complexities),
            )
        if optimization_opportunities:
            logger.info(
                "Pipeline: brute-force detection — %d optimisation(s) found",
                len(optimization_opportunities),
            )

        # ── Step 7c: Build visualization data (Day 15, sync, <1ms) ────────
        visualization = ComplexityVisualizer.build(function_complexities)
        if visualization:
            logger.info(
                "Pipeline: visualization — %d function(s), scores=%s",
                len(visualization.labels),
                visualization.complexity_scores,
            )

        complexity = ComplexityResult(
            time_complexity=complexity_result.time_complexity,
            space_complexity=complexity_result.space_complexity,
            explanation=complexity_result.explanation,
            brute_force_alternative=complexity_result.suggestion,
            function_complexities=function_complexities,
            optimization_opportunities=optimization_opportunities,
            visualization=visualization,
        )

        # ── Step 7d: Generate narrative summary (Day 15, async LLM) ──────
        try:
            complexity.summary = await generate_summary(complexity)
            logger.info(
                "Pipeline: summary generated — %d chars",
                len(complexity.summary),
            )
        except Exception as exc:
            logger.warning("Pipeline: summary generation failed: %s", exc)

        # Compute score and summary
        score = self._compute_score(all_bugs, security, complexity)
        summary = self._synthesise_summary(all_bugs, security, complexity)

        # ── Step 8: Build response with timing ──────────────────────────
        elapsed_ms = int((time.perf_counter() - t_start) * 1000)

        response = CodeReviewResponse(
            bugs=all_bugs,
            security=security,
            complexity=complexity,
            summary=summary,
            overall_score=score,
            processing_time_ms=elapsed_ms,
        )

        # ── Step 9: Cache + Store ────────────────────────────────────────
        await self._cache.set(cache_key, response.model_dump(), ttl=3600)

        # Store in memory for security-report endpoint (Day 12)
        self._review_counter += 1
        review_id = str(self._review_counter)
        _review_store[review_id] = response
        # Also store as "latest" for convenience
        _review_store["latest"] = response

        logger.info(
            "Pipeline: complete — score=%d, bugs=%d, security=%d, time=%dms, review_id=%s",
            score,
            len(all_bugs),
            len(security),
            elapsed_ms,
            review_id,
        )

        return response

    # ── Static Analysis ──────────────────────────────────────────────────────

    def _run_static_analysis(self, code: str, language: str) -> list[BugFinding]:
        """
        Run static analyzers appropriate for the given language.

        - Python: AST-based analyzers (ASTAnalyzer, ComplexityChecker, StyleChecker)
        - JavaScript / Java: Regex-based PatternMatcher
        - Other languages: empty list (LLM-only analysis)

        Args:
            code: The source code to analyze.
            language: Programming language of the code.

        Returns:
            List of BugFinding objects with source="static".
        """
        lang = language.lower()
        findings: list[BugFinding] = []

        if lang == "python":
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
        else:
            for pf in self._pattern_matcher.match(code, lang):
                findings.append(
                    BugFinding(
                        line=pf.line,
                        severity=pf.severity,
                        message=pf.message,
                        suggestion=pf.suggestion,
                        source="static",
                    )
                )

        return findings

    # ── Exploit Enrichment (Day 12) ───────────────────────────────────────────

    async def _enrich_security_findings(
        self,
        findings: list[SecurityFinding],
        code: str,
        language: str,
    ) -> list[SecurityFinding]:
        """
        Enrich critical/high security findings with LLM-generated exploit
        explanations and remediation code snippets.

        Uses asyncio.gather() to process all eligible findings in parallel,
        reducing latency from O(n) to O(1) LLM calls.

        Medium/low findings are passed through unchanged (with only reference
        links added — no LLM cost).

        Args:
            findings: List of SecurityFinding objects.
            code:     Full source code for context extraction.
            language: Programming language of the code.

        Returns:
            List of SecurityFinding objects with enrichment fields populated.
        """
        if not findings:
            return findings

        # Run all exploit explanations in parallel via asyncio.gather()
        enriched = await asyncio.gather(
            *[
                self._exploit_explainer.explain(finding, code, language)
                for finding in findings
            ]
        )

        critical_high = sum(
            1 for f in enriched
            if f.severity in ("critical", "high") and f.exploit_scenario
        )
        logger.info(
            "Pipeline: enriched %d/%d findings with exploit scenarios",
            critical_high,
            len(findings),
        )

        return list(enriched)

    # ── Deduplication ────────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate_findings(findings: list[BugFinding]) -> list[BugFinding]:
        """
        Remove duplicate findings across static and LLM sources.

        Deduplication strategy:
            Two findings are considered duplicates if:
                1. They share the same line_number (or both are None), AND
                2. Their messages have >80% similarity (SequenceMatcher ratio)

            When a duplicate pair is found, we keep the static analyzer's
            finding (it has a precise line number from AST/regex) and discard
            the LLM duplicate.

        Why keep static over LLM?
            Static analyzers provide exact line numbers and deterministic
            results. LLM findings may hallucinate line numbers or give
            slightly different descriptions on each run.

        Args:
            findings: Combined list of static + LLM findings.

        Returns:
            Deduplicated list of BugFinding objects.
        """
        if not findings:
            return findings

        # Process findings: static first so they "win" during dedup
        static = [f for f in findings if f.source == "static"]
        llm = [f for f in findings if f.source == "llm"]

        # Start with all static findings (always kept)
        kept: list[BugFinding] = list(static)

        for llm_finding in llm:
            is_duplicate = False
            for static_finding in static:
                # Check same line (None matches None)
                if llm_finding.line == static_finding.line:
                    # Check message similarity
                    similarity = SequenceMatcher(
                        None,
                        llm_finding.message.lower(),
                        static_finding.message.lower(),
                    ).ratio()
                    if similarity > _SIMILARITY_THRESHOLD:
                        is_duplicate = True
                        logger.debug(
                            "Pipeline: dedup — discarding LLM finding "
                            "(line=%s, sim=%.0f%%): %s",
                            llm_finding.line,
                            similarity * 100,
                            llm_finding.message[:60],
                        )
                        break
            if not is_duplicate:
                kept.append(llm_finding)

        removed = len(findings) - len(kept)
        if removed:
            logger.info(
                "Pipeline: deduplicated %d finding(s) — %d → %d",
                removed,
                len(findings),
                len(kept),
            )

        return kept

    # ── Scoring ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(
        bugs: list[BugFinding],
        security: list[SecurityFinding],
        complexity: ComplexityResult,
    ) -> int:
        """
        Compute an overall quality score from 0–100.

        Formula:
            Start at 100.
            Subtract per bug:
                critical: -25
                high:     -15
                medium:   -7
                low:      -2
            Security findings count 1.5× their equivalent penalty.
            Clamp result to [0, 100].

        Args:
            bugs:       List of bug findings.
            security:   List of security findings.
            complexity: Complexity result (unused in scoring, reserved for future).

        Returns:
            Integer score clamped to [0, 100].
        """
        score = 100.0

        # Bug penalties
        for bug in bugs:
            penalty = _BUG_PENALTIES.get(bug.severity, 2)
            score -= penalty

        # Security penalties (1.5× multiplier)
        for sec in security:
            penalty = _BUG_PENALTIES.get(sec.severity, 2) * _SECURITY_MULTIPLIER
            score -= penalty

        return max(0, min(100, int(score)))

    # ── Sorting ──────────────────────────────────────────────────────────────

    @staticmethod
    def _sort_findings(findings: list[BugFinding]) -> list[BugFinding]:
        """
        Sort findings by severity (critical > high > medium > low),
        then by line number (ascending, None last).

        Args:
            findings: Unsorted list of BugFinding objects.

        Returns:
            Sorted list of BugFinding objects.
        """
        return sorted(
            findings,
            key=lambda f: (
                _SEVERITY_ORDER.get(f.severity, 99),
                f.line if f.line is not None else float("inf"),
            ),
        )

    # ── Summary ──────────────────────────────────────────────────────────────

    @staticmethod
    def _synthesise_summary(
        bugs: list[BugFinding],
        security: list[SecurityFinding],
        complexity: ComplexityResult,
    ) -> str:
        """
        Generate a human-readable summary from the pipeline results.
        """
        parts = []

        # Bug summary
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
                + (
                    f" — {critical_bugs} critical, {high_bugs} high"
                    if critical_bugs or high_bugs
                    else ""
                )
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
