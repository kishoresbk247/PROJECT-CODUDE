"""
CoDude — Solution Generator (Day 14)

For each detected brute-force pattern, calls the LLM with a targeted
prompt that produces:
    (a) A 3-sentence explanation of why the current approach is suboptimal
    (b) An optimised implementation in the same language
    (c) The new Big-O complexity

Key insight — why targeted prompts beat generic "optimise this" prompts:
    Generic: "Optimise this code" → vague advice, often wrong
    Targeted: "This is a two-sum problem using nested loops — provide a
              hash map solution in Python" → precise, correct code

    The AST analyzer identifies the pattern, the pattern library supplies
    the targeted prompt, and the LLM generates the solution. This is
    AI-augmented static analysis in action.

Usage:
    generator = SolutionGenerator()
    opportunity = await generator.generate(detected_pattern, language)
"""

import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.models.review import OptimizationOpportunity
from app.services.complexity.brute_force_detector import DetectedPattern
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# ── Structured Output Schema for the LLM ─────────────────────────────────────

class OptimizationSuggestionSchema(BaseModel):
    """Schema for the LLM's optimisation suggestion response."""

    explanation: str = Field(
        ...,
        description=(
            "A 3-sentence explanation of WHY the current approach is "
            "suboptimal and HOW the suggested approach improves it."
        ),
    )
    optimized_code: str = Field(
        ...,
        description=(
            "The complete optimised implementation in the same language. "
            "Must be a working, drop-in replacement using the same "
            "function signature."
        ),
    )
    new_time_complexity: str = Field(
        ...,
        description="Big-O time complexity of the optimised solution (e.g. 'O(n)').",
    )
    new_space_complexity: str = Field(
        ...,
        description="Big-O space complexity of the optimised solution (e.g. 'O(n)').",
    )


# ── Prompt Template ──────────────────────────────────────────────────────────
# NOTE: JSON curly braces must be escaped as {{ }} for LangChain templates.

_OPTIMIZATION_SYSTEM = """\
You are a **senior algorithms expert** specialising in code optimisation. \
You have deep knowledge of data structures, algorithm design patterns, \
and computational complexity theory.

Your task is to provide an optimised solution for a given brute-force \
implementation. You MUST:

1. Explain in exactly 3 sentences WHY the current approach is suboptimal \
and HOW your suggested approach improves it.
2. Provide a complete, working optimised implementation that is a \
drop-in replacement (same function name and parameters).
3. State the new Big-O time and space complexity.

## Rules
- The optimised code MUST be correct and handle edge cases.
- Keep the same function signature (name, parameters, return type).
- Use idiomatic code for the given language.
- Do NOT add unnecessary comments — the code should be self-explanatory.
- Do NOT import external libraries unless absolutely necessary.\
"""

_OPTIMIZATION_HUMAN = """\
## Current Implementation ({language})

```{language}
{current_code}
```

## Pattern Detected
{pattern_description}

## Current Complexity
- Time: {current_complexity}
- Space: {current_space}

## Optimisation Instruction
{optimization_prompt}

Provide the optimised solution as structured JSON.\
"""

_OPTIMIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _OPTIMIZATION_SYSTEM),
    ("human", _OPTIMIZATION_HUMAN),
])


class SolutionGenerator:
    """
    Generates optimised code solutions for detected brute-force patterns
    using targeted LLM prompts.

    The key insight is that we don't ask the LLM to "optimise" generically.
    Instead, we tell it exactly which algorithm pattern was detected and
    what the optimal approach is. This yields precise, correct solutions.

    Usage:
        generator = SolutionGenerator()
        opportunity = await generator.generate(detected, "python")
    """

    def __init__(self) -> None:
        """Initialise LLM service and LCEL chain."""
        self._llm_service = LLMService()
        self._chain = (
            _OPTIMIZATION_PROMPT
            | self._llm_service.with_structured_output(
                OptimizationSuggestionSchema
            )
        )

    async def generate(
        self,
        detected: DetectedPattern,
        language: str = "python",
    ) -> Optional[OptimizationOpportunity]:
        """
        Generate an OptimizationOpportunity for a detected brute-force pattern.

        Calls the LLM with a targeted prompt built from the pattern library
        entry. Returns None if the LLM call fails.

        Args:
            detected: A DetectedPattern from the BruteForceDetector.
            language: Programming language of the code.

        Returns:
            An OptimizationOpportunity with explanation, code, and complexity,
            or None on failure.
        """
        pattern = detected.pattern_entry

        try:
            logger.info(
                "SolutionGenerator: generating optimisation for '%s' "
                "(pattern='%s', %s)",
                detected.function_name,
                detected.pattern_name,
                pattern["improvement_factor"],
            )

            result: OptimizationSuggestionSchema = await self._chain.ainvoke({
                "language": language,
                "current_code": detected.function_code,
                "pattern_description": pattern["description"],
                "current_complexity": pattern["brute_force_complexity"],
                "current_space": "O(1)",  # brute-force typically uses O(1) space
                "optimization_prompt": pattern["template_prompt"],
            })

            opportunity = OptimizationOpportunity(
                pattern_name=detected.pattern_name,
                current_complexity=pattern["brute_force_complexity"],
                optimal_complexity=pattern["optimal_complexity"],
                improvement_factor=pattern["improvement_factor"],
                suggested_approach=pattern["optimal_approach"],
                explanation=result.explanation,
                example_code=result.optimized_code,
                function_name=detected.function_name,
                line_start=detected.line_start,
                line_end=detected.line_end,
            )

            logger.info(
                "SolutionGenerator: generated %d-char optimised code for '%s'",
                len(result.optimized_code),
                detected.function_name,
            )

            return opportunity

        except Exception as exc:
            logger.warning(
                "SolutionGenerator: LLM call failed for '%s': %s",
                detected.function_name,
                exc,
            )
            # Return a partial opportunity without LLM-generated code
            return OptimizationOpportunity(
                pattern_name=detected.pattern_name,
                current_complexity=pattern["brute_force_complexity"],
                optimal_complexity=pattern["optimal_complexity"],
                improvement_factor=pattern["improvement_factor"],
                suggested_approach=pattern["optimal_approach"],
                explanation=(
                    f"The current {pattern['brute_force_complexity']} approach "
                    f"can be improved to {pattern['optimal_complexity']} using "
                    f"{pattern['optimal_approach']}."
                ),
                example_code=None,
                function_name=detected.function_name,
                line_start=detected.line_start,
                line_end=detected.line_end,
            )
