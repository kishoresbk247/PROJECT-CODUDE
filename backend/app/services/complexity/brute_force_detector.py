"""
CoDude — Brute Force Detector (Day 14)

Cross-references AST complexity results with ALGORITHM_PATTERNS to identify
code that uses a brute-force approach when a faster algorithm exists.

Strategy:
    1. Take FunctionComplexityResult objects from the AST analyzer
    2. For each function, check its loop depth, recursion flags, and
       variable names against each pattern's detection_hints
    3. Score each pattern match (0.0 – 1.0) based on how many hints match
    4. Return OptimizationOpportunity objects for matches above threshold

The detector does NOT suggest optimisations itself — it identifies
*which* pattern applies. The SolutionGenerator then uses the pattern's
template_prompt to get a precise, targeted optimisation from the LLM.

Usage:
    detector = BruteForceDetector()
    opportunities = detector.detect(ast_results, code)
"""

import logging
import re
from dataclasses import dataclass

from app.services.complexity.ast_complexity import FunctionComplexityResult
from app.services.complexity.pattern_library import (
    ALGORITHM_PATTERNS,
    PatternEntry,
)

logger = logging.getLogger(__name__)

# Minimum match score to report an optimisation opportunity
_MATCH_THRESHOLD = 0.5


@dataclass
class DetectedPattern:
    """
    Internal result from pattern matching before LLM enrichment.

    Attributes:
        function_name:   Name of the function with the detected pattern.
        pattern_name:    Key from ALGORITHM_PATTERNS.
        pattern_entry:   The full pattern entry dict.
        match_score:     Confidence score (0.0 – 1.0).
        function_code:   The source code of the matched function.
        line_start:      First line of the function.
        line_end:        Last line of the function.
    """

    function_name: str
    pattern_name: str
    pattern_entry: PatternEntry
    match_score: float
    function_code: str
    line_start: int
    line_end: int


class BruteForceDetector:
    """
    Detects brute-force algorithm patterns by cross-referencing AST
    complexity results with the ALGORITHM_PATTERNS library.

    Usage:
        detector = BruteForceDetector()
        detected = detector.detect(ast_results, source_code)
    """

    def detect(
        self,
        ast_results: list[FunctionComplexityResult],
        source_code: str,
    ) -> list[DetectedPattern]:
        """
        Scan AST results for brute-force patterns.

        Args:
            ast_results:  List of FunctionComplexityResult from AST analyzer.
            source_code:  Full source code (for extracting function bodies).

        Returns:
            List of DetectedPattern objects for functions that match a
            brute-force pattern with a score above the threshold.
        """
        if not ast_results:
            return []

        detected: list[DetectedPattern] = []

        for result in ast_results:
            # Skip already-optimal functions (O(1), O(log n), O(n) with hash)
            if self._is_already_optimal(result):
                continue

            # Extract the function's source code
            func_code = self._extract_function_code(
                source_code, result.line_start, result.line_end
            )

            # Try matching each pattern
            best_match: DetectedPattern | None = None
            best_score = 0.0

            for pattern_name, pattern_entry in ALGORITHM_PATTERNS.items():
                score = self._score_match(result, func_code, pattern_entry)

                if score > best_score and score >= _MATCH_THRESHOLD:
                    best_score = score
                    best_match = DetectedPattern(
                        function_name=result.function_name,
                        pattern_name=pattern_name,
                        pattern_entry=pattern_entry,
                        match_score=score,
                        function_code=func_code,
                        line_start=result.line_start,
                        line_end=result.line_end,
                    )

            if best_match is not None:
                detected.append(best_match)
                logger.info(
                    "BruteForceDetector: '%s' matches pattern '%s' "
                    "(score=%.2f, %s → %s)",
                    result.function_name,
                    best_match.pattern_name,
                    best_match.match_score,
                    best_match.pattern_entry["brute_force_complexity"],
                    best_match.pattern_entry["optimal_complexity"],
                )

        logger.info(
            "BruteForceDetector: scanned %d function(s), found %d optimisation(s)",
            len(ast_results),
            len(detected),
        )

        return detected

    @staticmethod
    def _is_already_optimal(result: FunctionComplexityResult) -> bool:
        """
        Quick check: skip functions that are already using optimal approaches.

        Functions with O(1), O(log n), or O(n) with hash lookups are
        unlikely to benefit from optimisation suggestions.
        """
        optimal_complexities = {"O(1)", "O(log n)"}

        if result.time_complexity in optimal_complexities:
            return True

        # O(n) with hash lookups is already the optimal pattern
        if result.time_complexity == "O(n)" and result.has_hash_lookup_in_loop:
            return True

        return False

    @staticmethod
    def _score_match(
        result: FunctionComplexityResult,
        func_code: str,
        pattern: PatternEntry,
    ) -> float:
        """
        Score how well a function matches a brute-force pattern.

        Scoring rubric (0.0 – 1.0):
            - Loop depth match:       +0.40 (most important signal)
            - Keyword hint matches:   +0.35 (scaled by fraction matched)
            - Recursion flag match:   +0.15
            - Hash lookup mismatch:   +0.10

        Args:
            result:    AST analysis result for the function.
            func_code: Source code of the function.
            pattern:   The pattern entry to match against.

        Returns:
            Float score between 0.0 and 1.0.
        """
        hints = pattern["detection_hints"]
        score = 0.0

        # ── Loop depth match (0.40 weight) ───────────────────────────────
        expected_depth = hints.get("max_loop_depth")
        if expected_depth is not None:
            if result.max_loop_depth == expected_depth:
                score += 0.40
            elif result.max_loop_depth > expected_depth:
                # Deeper nesting still qualifies (worse than expected)
                score += 0.30
        else:
            # No depth requirement — give partial credit if there are loops
            if result.max_loop_depth > 0:
                score += 0.20

        # ── Keyword hint matches (0.35 weight) ──────────────────────────
        keyword_hints = hints.get("keyword_hints", [])
        if keyword_hints:
            code_lower = func_code.lower()
            matched = sum(
                1 for kw in keyword_hints
                if kw.lower() in code_lower
            )
            fraction = matched / len(keyword_hints)
            score += 0.35 * fraction

        # ── Recursion flag match (0.15 weight) ──────────────────────────
        expected_recursion = hints.get("has_recursion")
        if expected_recursion is not None:
            if result.has_recursion == expected_recursion:
                score += 0.15

        # ── Hash lookup mismatch (0.10 weight) ──────────────────────────
        expected_hash = hints.get("has_hash_lookup_in_loop")
        if expected_hash is not None:
            if result.has_hash_lookup_in_loop == expected_hash:
                score += 0.10

        return min(score, 1.0)

    @staticmethod
    def _extract_function_code(
        source_code: str, line_start: int, line_end: int
    ) -> str:
        """Extract function source code from the full source by line range."""
        lines = source_code.splitlines()
        return "\n".join(lines[line_start - 1 : line_end])
