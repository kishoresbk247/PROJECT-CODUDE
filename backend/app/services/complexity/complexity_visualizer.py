"""
CoDude — Complexity Visualizer (Day 15)

Converts list[FunctionComplexity] into a ComplexityVisualization object
that the frontend can use directly for bar charts, radar charts, and
comparison tables.

Key concept — ordinalization of categorical values:
    Big-O strings like "O(n²)" are categorical — you can't sort, chart,
    or compute averages on them. By mapping each to an integer score
    (1–6), we unlock numeric operations:

        O(1)       → 1  (constant)
        O(log n)   → 2  (logarithmic)
        O(n)       → 3  (linear)
        O(n log n) → 4  (linearithmic)
        O(n²)      → 5  (quadratic)
        O(2ⁿ)      → 6  (exponential)

    This pattern is used everywhere:
        - Star ratings in recommendation systems
        - TF-IDF in NLP
        - Feature engineering in ML pipelines

Usage:
    from app.services.complexity.complexity_visualizer import ComplexityVisualizer
    visualizer = ComplexityVisualizer()
    viz = visualizer.build(function_complexities)
"""

import logging
import re
from typing import Optional

from app.models.review import (
    ComplexityVisualization,
    FunctionComplexity,
)

logger = logging.getLogger(__name__)

# ── Complexity Score Mapping ─────────────────────────────────────────────────
# Ordered by computational cost, lowest to highest.
# Covers all standard Big-O classes encountered in practice.

_COMPLEXITY_SCORES: dict[str, int] = {
    "O(1)": 1,
    "O(log n)": 2,
    "O(n)": 3,
    "O(n log n)": 4,
    "O(n²)": 5,
    "O(n^2)": 5,
    "O(2ⁿ)": 6,
    "O(2^n)": 6,
}

# Regex patterns for fuzzy matching when exact lookup fails.
# Handles variations like "O(n²)", "O(n^2)", "O(n * log n)", etc.
_FUZZY_PATTERNS: list[tuple[str, int]] = [
    (r"O\(1\)", 1),
    (r"O\(log\s*n\)", 2),
    (r"O\(n\s*\*?\s*log\s*n\)", 4),    # Must come before O(n)
    (r"O\(n\s*log\s*n\)", 4),           # O(n log n) without *
    (r"O\(n\)", 3),
    (r"O\(n[\u00b2²]\)", 5),            # O(n²)
    (r"O\(n\^2\)", 5),                  # O(n^2)
    (r"O\(n[\u00b3³]\)", 5),            # O(n³) — mapped to 5 (quadratic bucket)
    (r"O\(n\^3\)", 5),                  # O(n^3)
    (r"O\(2[\u207f]\)", 6),             # O(2ⁿ)
    (r"O\(2\^n\)", 6),                  # O(2^n)
    (r"O\(n!\)", 6),                    # O(n!) — treated as exponential
]


def complexity_to_score(complexity_str: str) -> int:
    """
    Convert a Big-O complexity string to a numeric score (1–6).

    Uses exact lookup first, then fuzzy regex matching for variations.
    Returns 3 (linear) as a safe default for unrecognised strings.

    Scoring:
        O(1)       → 1
        O(log n)   → 2
        O(n)       → 3
        O(n log n) → 4
        O(n²)      → 5
        O(2ⁿ)      → 6

    Args:
        complexity_str: A Big-O notation string (e.g. "O(n²)", "O(n^2)").

    Returns:
        Integer score between 1 and 6.

    Examples:
        >>> complexity_to_score("O(n²)")
        5
        >>> complexity_to_score("O(log n)")
        2
        >>> complexity_to_score("O(n * log n)")
        4
    """
    # Step 1: Exact lookup (fastest path)
    normalized = complexity_str.strip()
    if normalized in _COMPLEXITY_SCORES:
        return _COMPLEXITY_SCORES[normalized]

    # Step 2: Fuzzy regex matching (handles format variations)
    for pattern, score in _FUZZY_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return score

    # Step 3: Default to linear (safe middle-ground)
    logger.warning(
        "ComplexityVisualizer: unrecognised complexity '%s' — defaulting to 3",
        complexity_str,
    )
    return 3


class ComplexityVisualizer:
    """
    Converts per-function complexity analysis into frontend-ready
    visualization data.

    Produces a ComplexityVisualization with parallel arrays:
        - labels:             function names
        - time_complexities:  Big-O strings
        - space_complexities: Big-O strings
        - complexity_scores:  numeric scores (1–6)

    This shape is optimised for Chart.js / D3.js / Recharts consumption:
        labels → x-axis, complexity_scores → y-axis.

    Usage:
        visualizer = ComplexityVisualizer()
        viz = visualizer.build(function_complexities)
    """

    @staticmethod
    def build(
        functions: list[FunctionComplexity],
    ) -> Optional[ComplexityVisualization]:
        """
        Build a ComplexityVisualization from a list of FunctionComplexity objects.

        Returns None if the input list is empty (no chart data to show).

        Args:
            functions: List of FunctionComplexity objects from the analyzer.

        Returns:
            ComplexityVisualization ready for frontend charting, or None.
        """
        if not functions:
            return None

        labels = [fc.function_name for fc in functions]
        time_complexities = [fc.time_complexity for fc in functions]
        space_complexities = [fc.space_complexity for fc in functions]
        complexity_scores = [
            complexity_to_score(fc.time_complexity) for fc in functions
        ]

        logger.info(
            "ComplexityVisualizer: built chart data for %d function(s) — "
            "scores=%s",
            len(functions),
            complexity_scores,
        )

        return ComplexityVisualization(
            labels=labels,
            time_complexities=time_complexities,
            space_complexities=space_complexities,
            complexity_scores=complexity_scores,
        )
