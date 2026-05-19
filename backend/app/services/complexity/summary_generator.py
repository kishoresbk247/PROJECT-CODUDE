"""
CoDude — Complexity Summary Generator (Day 15)

LLM-powered service that generates a 3–4 sentence plain-English executive
summary of the per-function complexity analysis.

Why LLM-generated summaries instead of templates?
    Template-based summaries are rigid: "Function X is O(n²), function Y is O(n)."
    LLM summaries are contextual: "This module is dominated by sort_users()
    which runs in O(n²) time. Consider replacing with Python's built-in
    Timsort for an immediate O(n log n) improvement."

    The LLM receives structured data (function names, complexities, scores)
    and produces a narrative that highlights:
        1. The dominant bottleneck function
        2. Which functions are already optimal
        3. Actionable improvement suggestions

Usage:
    from app.services.complexity.summary_generator import generate_summary
    summary = await generate_summary(complexity_result)
"""

import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.models.review import ComplexityResult
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# ── Prompt Template ──────────────────────────────────────────────────────────

_SUMMARY_SYSTEM = """\
You are a **senior software architect** writing an executive summary of a \
code complexity analysis for a development team. Your summaries are concise, \
actionable, and use plain English that non-specialists can understand.

## Rules
- Write EXACTLY 3–4 sentences.
- Sentence 1: Identify the dominant bottleneck (highest complexity function).
- Sentence 2: Mention how many functions were analyzed and their overall \
complexity distribution (how many are optimal vs. suboptimal).
- Sentence 3: Provide ONE specific, actionable improvement suggestion for \
the worst-performing function.
- Sentence 4 (optional): Note any functions that are already optimal.
- Use Big-O notation naturally (e.g. "runs in O(n²) time").
- Do NOT use bullet points or markdown formatting — write flowing prose.
- Do NOT start with "This module" if there's a more specific description.\
"""

_SUMMARY_HUMAN = """\
Here is the per-function complexity analysis:

{analysis_data}

Overall complexity: {overall_time} time, {overall_space} space.

Write a 3–4 sentence plain-English executive summary.\
"""

_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _SUMMARY_SYSTEM),
    ("human", _SUMMARY_HUMAN),
])


def _format_analysis_data(result: ComplexityResult) -> str:
    """
    Format ComplexityResult into a structured text block for the LLM prompt.

    Args:
        result: The ComplexityResult with per-function data.

    Returns:
        Formatted string listing each function's complexity.
    """
    if not result.function_complexities:
        return "No per-function analysis available."

    lines = []
    for fc in result.function_complexities:
        lines.append(
            f"- {fc.function_name}() "
            f"[lines {fc.line_start}–{fc.line_end}]: "
            f"time={fc.time_complexity}, space={fc.space_complexity}, "
            f"confidence={fc.confidence}"
        )

    if result.optimization_opportunities:
        lines.append("\nOptimization opportunities detected:")
        for opp in result.optimization_opportunities:
            lines.append(
                f"- {opp.function_name}(): {opp.improvement_factor} "
                f"via {opp.suggested_approach}"
            )

    return "\n".join(lines)


def _generate_fallback_summary(result: ComplexityResult) -> str:
    """
    Generate a template-based summary when LLM is unavailable.

    This is the fallback path — produces a correct but less elegant
    summary using string formatting instead of LLM generation.

    Args:
        result: The ComplexityResult with per-function data.

    Returns:
        A 2–3 sentence plain-English summary string.
    """
    funcs = result.function_complexities
    if not funcs:
        return (
            f"Overall complexity is {result.time_complexity} time and "
            f"{result.space_complexity} space. {result.explanation}"
        )

    # Find the worst-performing function (highest complexity string)
    from app.services.complexity.complexity_visualizer import complexity_to_score

    worst = max(funcs, key=lambda f: complexity_to_score(f.time_complexity))
    optimal_count = sum(
        1 for f in funcs
        if complexity_to_score(f.time_complexity) <= 2
    )

    parts = [
        f"The dominant bottleneck is {worst.function_name}() which runs in "
        f"{worst.time_complexity} time.",
        f"Analyzed {len(funcs)} function(s) — "
        f"{optimal_count} are already optimal (O(log n) or better).",
    ]

    if result.optimization_opportunities:
        opp = result.optimization_opportunities[0]
        parts.append(
            f"Consider {opp.suggested_approach.lower()} for "
            f"{opp.function_name}() to improve from "
            f"{opp.current_complexity} to {opp.optimal_complexity}."
        )

    return " ".join(parts)


async def generate_summary(
    result: ComplexityResult,
) -> str:
    """
    Generate a plain-English executive summary of the complexity analysis.

    Uses the LLM with a targeted prompt to produce a 3–4 sentence narrative
    summary. Falls back to template-based generation if the LLM call fails.

    Args:
        result: The ComplexityResult containing per-function analysis.

    Returns:
        A 3–4 sentence plain-English summary string.
    """
    if not result.function_complexities:
        return (
            f"Overall complexity is {result.time_complexity} time and "
            f"{result.space_complexity} space. {result.explanation}"
        )

    analysis_data = _format_analysis_data(result)

    try:
        llm_service = LLMService()
        chain = (
            _SUMMARY_PROMPT
            | llm_service.with_structured_output(SummarySchema)
        )

        response: SummarySchema = await chain.ainvoke({
            "analysis_data": analysis_data,
            "overall_time": result.time_complexity,
            "overall_space": result.space_complexity,
        })

        summary = response.summary.strip()
        logger.info(
            "SummaryGenerator: LLM generated %d-char summary", len(summary)
        )
        return summary

    except Exception as exc:
        logger.warning(
            "SummaryGenerator: LLM call failed (%s) — using fallback", exc
        )
        return _generate_fallback_summary(result)


# ── Structured Output Schema ────────────────────────────────────────────────

from pydantic import BaseModel, Field


class SummarySchema(BaseModel):
    """Schema for the LLM's complexity summary response."""

    summary: str = Field(
        ...,
        description=(
            "A 3–4 sentence plain-English executive summary of the "
            "complexity analysis. No bullet points or markdown."
        ),
    )
