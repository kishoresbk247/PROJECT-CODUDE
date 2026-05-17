"""
CoDude — Algorithm Pattern Library (Day 14)

Defines ALGORITHM_PATTERNS: a dictionary mapping recognisable brute-force
coding patterns to their algorithmically superior alternatives.

Design rationale:
    When you ask an LLM to "optimise this code," you get vague advice.
    When you tell it "this is a two-sum problem currently solved with nested
    loops — provide a hash map solution in Python," you get a precise,
    correct implementation.

    Pattern recognition (done by our AST analyzer) + targeted prompts
    (done by the LLM) = a tool that's more useful than either alone.

    This is the "AI-augmented static analysis" architecture used by
    Copilot, Cursor, and Tabnine.

Each pattern entry contains:
    - description:             Human-readable description of the pattern
    - detection_hints:         AST features that trigger this pattern
    - brute_force_complexity:  Big-O of the naive approach
    - optimal_approach:        Name of the optimal algorithm / data structure
    - optimal_complexity:      Big-O of the optimal approach
    - improvement_factor:      e.g. "O(n²) → O(n)"
    - template_prompt:         Targeted LLM prompt for generating the optimised code

Usage:
    from app.services.complexity.pattern_library import ALGORITHM_PATTERNS
    pattern = ALGORITHM_PATTERNS["nested_loop_two_sum"]
"""

from typing import TypedDict


class PatternEntry(TypedDict):
    """Type definition for a single algorithm pattern entry."""

    description: str
    detection_hints: dict[str, object]
    brute_force_complexity: str
    optimal_approach: str
    optimal_complexity: str
    improvement_factor: str
    template_prompt: str


# ── Algorithm Patterns Dictionary ────────────────────────────────────────────
#
# Each key is a snake_case identifier for the pattern.
# detection_hints maps AST features to expected values:
#   - max_loop_depth:          int, nested loop depth
#   - has_recursion:           bool
#   - has_binary_search:       bool
#   - has_hash_lookup_in_loop: bool
#   - keyword_hints:           list[str], variable/function name substrings
#                              that suggest a specific problem type

ALGORITHM_PATTERNS: dict[str, PatternEntry] = {
    # ── 1. Two-Sum / Pair Finding ────────────────────────────────────────
    "nested_loop_two_sum": {
        "description": "Nested loops checking all pairs (e.g., two-sum, pair finding)",
        "detection_hints": {
            "max_loop_depth": 2,
            "has_hash_lookup_in_loop": False,
            "keyword_hints": ["sum", "pair", "target", "complement"],
        },
        "brute_force_complexity": "O(n²)",
        "optimal_approach": "Hash map (single pass)",
        "optimal_complexity": "O(n)",
        "improvement_factor": "O(n²) → O(n)",
        "template_prompt": (
            "This is a two-sum / pair-finding problem currently solved with "
            "nested loops iterating over all pairs. Provide an optimised "
            "hash map solution that solves it in a single pass with O(n) time "
            "and O(n) space. Use the same function signature."
        ),
    },
    # ── 2. Linear Search on Sorted Data ──────────────────────────────────
    "sorted_search": {
        "description": "Linear scan over sorted/searchable data instead of binary search",
        "detection_hints": {
            "max_loop_depth": 1,
            "has_binary_search": False,
            "keyword_hints": ["search", "find", "index", "sorted", "lookup"],
        },
        "brute_force_complexity": "O(n)",
        "optimal_approach": "Binary search",
        "optimal_complexity": "O(log n)",
        "improvement_factor": "O(n) → O(log n)",
        "template_prompt": (
            "This code performs a linear search over data that could be "
            "searched with binary search. Provide a binary search "
            "implementation with O(log n) time complexity. Assume the "
            "input is sorted or can be sorted as a preprocessing step."
        ),
    },
    # ── 3. Naive Substring / Pattern Matching ────────────────────────────
    "repeated_substring": {
        "description": "Naive nested-loop substring or pattern matching",
        "detection_hints": {
            "max_loop_depth": 2,
            "keyword_hints": ["substring", "pattern", "match", "find", "window"],
        },
        "brute_force_complexity": "O(n × m)",
        "optimal_approach": "KMP / sliding window / Rabin-Karp",
        "optimal_complexity": "O(n + m)",
        "improvement_factor": "O(n × m) → O(n + m)",
        "template_prompt": (
            "This code uses a naive nested-loop approach for substring or "
            "pattern matching. Provide an optimised solution using the "
            "sliding window technique or KMP algorithm with O(n + m) "
            "time complexity."
        ),
    },
    # ── 4. Bubble / Selection / Insertion Sort ───────────────────────────
    "quadratic_sort": {
        "description": "Quadratic sorting algorithm (bubble, selection, or insertion sort)",
        "detection_hints": {
            "max_loop_depth": 2,
            "keyword_hints": ["sort", "swap", "bubble", "selection", "insertion"],
        },
        "brute_force_complexity": "O(n²)",
        "optimal_approach": "Merge sort / Timsort (built-in sorted())",
        "optimal_complexity": "O(n log n)",
        "improvement_factor": "O(n²) → O(n log n)",
        "template_prompt": (
            "This code implements a quadratic sorting algorithm (O(n²)). "
            "Provide an optimised O(n log n) solution. In Python, prefer "
            "the built-in sorted() or list.sort() which uses Timsort. "
            "If a custom sort is needed, provide a merge sort implementation."
        ),
    },
    # ── 5. Duplicate Detection via Nested Loops ──────────────────────────
    "nested_loop_duplicate": {
        "description": "Nested loops to find duplicates instead of using a set",
        "detection_hints": {
            "max_loop_depth": 2,
            "has_hash_lookup_in_loop": False,
            "keyword_hints": ["duplicate", "unique", "distinct", "seen"],
        },
        "brute_force_complexity": "O(n²)",
        "optimal_approach": "Hash set (single pass)",
        "optimal_complexity": "O(n)",
        "improvement_factor": "O(n²) → O(n)",
        "template_prompt": (
            "This code uses nested loops to detect duplicates. Provide an "
            "optimised hash set solution that detects duplicates in a single "
            "pass with O(n) time and O(n) space."
        ),
    },
    # ── 6. Naive Fibonacci (Exponential Recursion) ───────────────────────
    "exponential_recursion": {
        "description": "Recursive solution without memoisation (e.g., naive Fibonacci)",
        "detection_hints": {
            "has_recursion": True,
            "has_hash_lookup_in_loop": False,
            "keyword_hints": ["fib", "fibonacci", "recursi"],
        },
        "brute_force_complexity": "O(2ⁿ)",
        "optimal_approach": "Dynamic programming / memoisation",
        "optimal_complexity": "O(n)",
        "improvement_factor": "O(2ⁿ) → O(n)",
        "template_prompt": (
            "This code uses naive recursion without memoisation, resulting in "
            "exponential time complexity. Provide an optimised solution using "
            "dynamic programming (bottom-up) or memoisation (top-down with "
            "@functools.lru_cache) to achieve O(n) time."
        ),
    },
    # ── 7. Nested Loop Max/Min Subarray ──────────────────────────────────
    "nested_loop_subarray": {
        "description": "Nested loops for max/min subarray instead of Kadane's algorithm",
        "detection_hints": {
            "max_loop_depth": 2,
            "keyword_hints": ["subarray", "max_sum", "min_sum", "kadane", "contiguous"],
        },
        "brute_force_complexity": "O(n²)",
        "optimal_approach": "Kadane's algorithm (single pass)",
        "optimal_complexity": "O(n)",
        "improvement_factor": "O(n²) → O(n)",
        "template_prompt": (
            "This code uses nested loops to find the maximum subarray sum. "
            "Provide an optimised solution using Kadane's algorithm with "
            "O(n) time and O(1) space."
        ),
    },
    # ── 8. Repeated Linear Lookups ───────────────────────────────────────
    "repeated_linear_lookup": {
        "description": "Multiple list.index() / 'in list' lookups instead of set/dict",
        "detection_hints": {
            "max_loop_depth": 1,
            "has_hash_lookup_in_loop": False,
            "keyword_hints": ["index", "count", "in "],
        },
        "brute_force_complexity": "O(n × m)",
        "optimal_approach": "Pre-built hash set for O(1) lookups",
        "optimal_complexity": "O(n + m)",
        "improvement_factor": "O(n × m) → O(n + m)",
        "template_prompt": (
            "This code performs repeated membership tests against a list "
            "(O(n) per lookup). Provide an optimised solution that converts "
            "the lookup target to a set first (O(n) build, O(1) per lookup) "
            "to achieve O(n + m) total time."
        ),
    },
    # ── 9. Matrix Traversal with Redundant Recomputation ─────────────────
    "redundant_matrix_traversal": {
        "description": "Triple-nested loops with redundant computation on matrix",
        "detection_hints": {
            "max_loop_depth": 3,
            "keyword_hints": ["matrix", "grid", "row", "col", "dp"],
        },
        "brute_force_complexity": "O(n³)",
        "optimal_approach": "Dynamic programming / prefix sums",
        "optimal_complexity": "O(n²)",
        "improvement_factor": "O(n³) → O(n²)",
        "template_prompt": (
            "This code uses triple-nested loops over a matrix with redundant "
            "computation. Provide an optimised solution using dynamic "
            "programming or prefix sums to reduce time complexity from "
            "O(n³) to O(n²)."
        ),
    },
    # ── 10. String Concatenation in Loop ─────────────────────────────────
    "string_concat_in_loop": {
        "description": "String concatenation with += inside a loop (quadratic in Python)",
        "detection_hints": {
            "max_loop_depth": 1,
            "keyword_hints": ["concat", "string", "result", "output", "join"],
        },
        "brute_force_complexity": "O(n²)",
        "optimal_approach": "list.append() + ''.join() or io.StringIO",
        "optimal_complexity": "O(n)",
        "improvement_factor": "O(n²) → O(n)",
        "template_prompt": (
            "This code builds a string using += concatenation inside a loop. "
            "In Python, strings are immutable so each concatenation creates a "
            "new string, resulting in O(n²) total time. Provide an optimised "
            "solution using list.append() + ''.join() for O(n) performance."
        ),
    },
}


def get_pattern_names() -> list[str]:
    """Return all available pattern names."""
    return list(ALGORITHM_PATTERNS.keys())


def get_pattern(name: str) -> PatternEntry | None:
    """Look up a pattern by name. Returns None if not found."""
    return ALGORITHM_PATTERNS.get(name)
