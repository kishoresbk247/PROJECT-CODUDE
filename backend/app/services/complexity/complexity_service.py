"""
CoDude — Complexity Service (Day 14)

Orchestrator that combines AST-based pattern matching with selective LLM
analysis for per-function Big-O complexity annotation.

Strategy (hybrid approach):
    1. Run ASTComplexityAnalyzer on all functions (sync, <10ms, free)
    2. Run SpaceAnalyzer on all functions (sync, <10ms, free)
    3. For functions with confidence == "low", call the LLM complexity
       prompt for JUST that function (async, ~1.5s, ~$0.002/call)
    4. Return FunctionComplexity objects with combined results

Day 14 additions:
    5. Run BruteForceDetector to identify optimisation opportunities
    6. For detected patterns, run SolutionGenerator (targeted LLM prompts)
    7. Return OptimizationOpportunity objects alongside complexity results

This mirrors the hybrid AI/static analysis pattern from Day 12:
    - Static rules are the primary signal (fast, precise, free)
    - LLMs add contextual understanding for ambiguous cases
    - Cost scales with complexity, not code size

Usage:
    service = ComplexityService()
    complexities, opportunities = await service.analyze(code, language="python")
"""

import asyncio
import ast
import logging
from typing import Optional

from app.models.review import FunctionComplexity, OptimizationOpportunity
from app.services.complexity.ast_complexity import (
    ASTComplexityAnalyzer,
    FunctionComplexityResult,
)
from app.services.complexity.brute_force_detector import BruteForceDetector
from app.services.complexity.solution_generator import SolutionGenerator
from app.services.complexity.space_analyzer import SpaceAnalyzer
from app.services.llm_service import LLMService
from app.services.prompts.complexity_analysis import COMPLEXITY_ANALYSIS_PROMPT
from app.services.prompts.structured_output import ComplexityAnalysisSchema

logger = logging.getLogger(__name__)


class ComplexityService:
    """
    Orchestrates per-function Big-O complexity analysis using a hybrid
    approach: AST pattern matching first, LLM fallback for low-confidence.

    Day 14: Also detects brute-force patterns and generates optimised
    solution suggestions using targeted LLM prompts.

    Usage:
        service = ComplexityService()
        complexities, opportunities = await service.analyze(code, language="python")
    """

    def __init__(self) -> None:
        """Initialise analyzers, detector, generator, and LLM chain."""
        self._ast_analyzer = ASTComplexityAnalyzer()
        self._space_analyzer = SpaceAnalyzer()
        self._brute_force_detector = BruteForceDetector()
        self._solution_generator = SolutionGenerator()
        self._llm_service = LLMService()
        self._llm_chain = (
            COMPLEXITY_ANALYSIS_PROMPT
            | self._llm_service.with_structured_output(ComplexityAnalysisSchema)
        )

    async def analyze(
        self, code: str, language: str = "python"
    ) -> tuple[list[FunctionComplexity], list[OptimizationOpportunity]]:
        """
        Analyze per-function complexity using AST + optional LLM fallback,
        then detect brute-force patterns and generate optimisation suggestions.

        Steps:
            1. AST time complexity analysis for all functions
            2. AST space complexity analysis for all functions
            3. LLM enrichment for low-confidence functions only
            4. Merge into FunctionComplexity models
            5. Brute-force pattern detection (Day 14)
            6. Solution generation for detected patterns (Day 14)

        Args:
            code:     Source code to analyze.
            language: Programming language (AST only works for Python).

        Returns:
            Tuple of (FunctionComplexity list, OptimizationOpportunity list).
        """
        # ── Step 1: AST time complexity ─────────────────────────────────
        if language.lower() != "python":
            # For non-Python languages, use LLM-only analysis
            logger.info(
                "ComplexityService: non-Python language '%s' — using LLM-only",
                language,
            )
            results = await self._llm_only_analysis(code, language)
            return results, []  # No brute-force detection for non-Python

        time_results = self._ast_analyzer.analyze(code)
        if not time_results:
            logger.info("ComplexityService: no functions found in code")
            return [], []

        logger.info(
            "ComplexityService: AST found %d function(s)", len(time_results)
        )

        # ── Step 2: AST space complexity ────────────────────────────────
        space_results = self._space_analyzer.analyze_code(code)

        # ── Step 3: LLM enrichment for low-confidence ───────────────────
        enriched_results: list[FunctionComplexity] = []

        for time_result in time_results:
            space = space_results.get(time_result.function_name)
            space_complexity = space.space_complexity if space else "O(1)"
            space_reasoning = space.reasoning if space else "No space analysis available."

            if time_result.confidence == "low":
                # Extract just this function's code for a targeted LLM call
                func_code = self._extract_function_code(
                    code, time_result.line_start, time_result.line_end
                )
                llm_result = await self._llm_analyze_function(
                    func_code, language, time_result
                )
                if llm_result:
                    enriched_results.append(llm_result)
                    continue

            # Use AST result (high/medium confidence or LLM fallback failed)
            combined_reasoning = (
                f"**Time**: {time_result.reasoning}\n"
                f"**Space**: {space_reasoning}"
            )

            enriched_results.append(
                FunctionComplexity(
                    function_name=time_result.function_name,
                    line_start=time_result.line_start,
                    line_end=time_result.line_end,
                    time_complexity=time_result.time_complexity,
                    space_complexity=space_complexity,
                    confidence=time_result.confidence,
                    reasoning=combined_reasoning,
                )
            )

        logger.info(
            "ComplexityService: analyzed %d function(s) — %d high, %d medium, %d low confidence",
            len(enriched_results),
            sum(1 for r in enriched_results if r.confidence == "high"),
            sum(1 for r in enriched_results if r.confidence == "medium"),
            sum(1 for r in enriched_results if r.confidence == "low"),
        )

        # ── Step 5: Brute-force detection (Day 14) ──────────────────────
        detected_patterns = self._brute_force_detector.detect(
            time_results, code
        )

        # ── Step 6: Solution generation (Day 14) ────────────────────────
        opportunities: list[OptimizationOpportunity] = []
        if detected_patterns:
            # Run all solution generations in parallel
            gen_results = await asyncio.gather(
                *[
                    self._solution_generator.generate(dp, language)
                    for dp in detected_patterns
                ],
                return_exceptions=True,
            )
            for gen_result in gen_results:
                if isinstance(gen_result, OptimizationOpportunity):
                    opportunities.append(gen_result)
                elif isinstance(gen_result, Exception):
                    logger.warning(
                        "ComplexityService: solution generation failed: %s",
                        gen_result,
                    )

            logger.info(
                "ComplexityService: generated %d optimisation suggestion(s)",
                len(opportunities),
            )

        return enriched_results, opportunities

    async def _llm_analyze_function(
        self,
        func_code: str,
        language: str,
        ast_result: FunctionComplexityResult,
    ) -> Optional[FunctionComplexity]:
        """
        Call the LLM for a single low-confidence function.

        Only called when AST analysis can't determine complexity with
        sufficient confidence. This keeps LLM costs proportional to
        code complexity, not code size.

        Args:
            func_code:   Source code of just the function.
            language:    Programming language.
            ast_result:  The AST analysis result (used as fallback).

        Returns:
            FunctionComplexity with LLM-enhanced analysis, or None on failure.
        """
        try:
            logger.info(
                "ComplexityService: LLM call for low-confidence function '%s' "
                "(lines %d–%d)",
                ast_result.function_name,
                ast_result.line_start,
                ast_result.line_end,
            )

            result: ComplexityAnalysisSchema = await self._llm_chain.ainvoke(
                {"language": language, "code": func_code}
            )

            return FunctionComplexity(
                function_name=ast_result.function_name,
                line_start=ast_result.line_start,
                line_end=ast_result.line_end,
                time_complexity=result.time_complexity,
                space_complexity=result.space_complexity,
                confidence="medium",  # LLM-enhanced bumps from low → medium
                reasoning=(
                    f"**LLM-enhanced analysis** (AST confidence was low):\n"
                    f"{result.explanation}"
                ),
            )

        except Exception as exc:
            logger.warning(
                "ComplexityService: LLM call failed for '%s': %s",
                ast_result.function_name,
                exc,
            )
            return None

    async def _llm_only_analysis(
        self, code: str, language: str
    ) -> list[FunctionComplexity]:
        """
        Full LLM analysis for non-Python languages where AST isn't available.

        Returns a single FunctionComplexity for the entire code block.
        Per-function analysis for non-Python will be added in future days.

        Args:
            code:     Source code to analyze.
            language: Programming language.

        Returns:
            List with a single FunctionComplexity for the overall code.
        """
        try:
            result: ComplexityAnalysisSchema = await self._llm_chain.ainvoke(
                {"language": language, "code": code}
            )

            return [
                FunctionComplexity(
                    function_name="<overall>",
                    line_start=1,
                    line_end=code.count("\n") + 1,
                    time_complexity=result.time_complexity,
                    space_complexity=result.space_complexity,
                    confidence="medium",
                    reasoning=result.explanation,
                )
            ]

        except Exception as exc:
            logger.error("ComplexityService: LLM-only analysis failed: %s", exc)
            return []

    @staticmethod
    def _extract_function_code(code: str, line_start: int, line_end: int) -> str:
        """
        Extract function source code from the full source by line range.

        Args:
            code:       Full source code.
            line_start: First line (1-indexed).
            line_end:   Last line (1-indexed).

        Returns:
            The function's source code as a string.
        """
        lines = code.splitlines()
        return "\n".join(lines[line_start - 1 : line_end])
