"""
CoDude — Brute-Force Detection & Optimal Solution Tests (Day 14)

Tests:
    1. Pattern library has all 10 patterns with required keys
    2. BruteForceDetector matches nested-loop two-sum as brute-force
    3. BruteForceDetector skips already-optimal hash-map solution
    4. BruteForceDetector matches bubble sort as quadratic sort
    5. BruteForceDetector skips binary search (already O(log n))
    6. BruteForceDetector skips O(1) constant functions
    7. BruteForceDetector returns empty for no functions
    8. OptimizationOpportunity model validates correctly
    9. Pattern scoring: high score for strong match
    10. Pattern scoring: low score rejects weak match
    11. Deliverable: naive two-sum → detected with correct pattern
    12. Multiple functions: only brute-force ones are flagged

All tests use AST analysis + BruteForceDetector directly (no LLM calls)
to verify the pattern matching and detection logic.
"""

import pytest

from app.models.review import OptimizationOpportunity
from app.services.complexity.ast_complexity import ASTComplexityAnalyzer
from app.services.complexity.brute_force_detector import BruteForceDetector
from app.services.complexity.pattern_library import (
    ALGORITHM_PATTERNS,
    get_pattern,
    get_pattern_names,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def time_analyzer():
    """Create an ASTComplexityAnalyzer instance."""
    return ASTComplexityAnalyzer()


@pytest.fixture
def detector():
    """Create a BruteForceDetector instance."""
    return BruteForceDetector()


# ── Test Code Samples ───────────────────────────────────────────────────────

NAIVE_TWO_SUM = """\
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""

OPTIMAL_TWO_SUM = """\
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

BUBBLE_SORT = """\
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""

BINARY_SEARCH = """\
def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
"""

SIMPLE_GETTER = """\
def get_first(items):
    return items[0]
"""

CONTAINS_DUPLICATE_OPTIMAL = """\
def contains_duplicate(nums):
    seen = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
"""

NAIVE_DUPLICATE_CHECK = """\
def find_duplicate(arr):
    seen = False
    duplicate = None
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j]:
                seen = True
                duplicate = arr[i]
                return duplicate
    return None
"""

MIXED_FUNCTIONS = """\
def optimal_lookup(nums, target):
    seen = {}
    for num in nums:
        if target - num in seen:
            return True
        seen[num] = True
    return False

def get_value(x):
    return x * 2

def naive_pair_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""


# ── Pattern Library Tests ───────────────────────────────────────────────────

class TestPatternLibrary:
    """Tests for the ALGORITHM_PATTERNS dictionary."""

    def test_has_10_patterns(self):
        """Pattern library should have at least 10 entries."""
        assert len(ALGORITHM_PATTERNS) >= 10

    def test_all_patterns_have_required_keys(self):
        """Every pattern must have the 7 required keys."""
        required_keys = {
            "description",
            "detection_hints",
            "brute_force_complexity",
            "optimal_approach",
            "optimal_complexity",
            "improvement_factor",
            "template_prompt",
        }
        for name, entry in ALGORITHM_PATTERNS.items():
            missing = required_keys - set(entry.keys())
            assert not missing, f"Pattern '{name}' missing keys: {missing}"

    def test_get_pattern_returns_entry(self):
        """get_pattern should return the entry for a valid name."""
        entry = get_pattern("nested_loop_two_sum")
        assert entry is not None
        assert entry["brute_force_complexity"] == "O(n²)"
        assert entry["optimal_complexity"] == "O(n)"

    def test_get_pattern_returns_none_for_invalid(self):
        """get_pattern should return None for unknown pattern."""
        assert get_pattern("nonexistent_pattern") is None

    def test_get_pattern_names(self):
        """get_pattern_names should return all pattern keys."""
        names = get_pattern_names()
        assert "nested_loop_two_sum" in names
        assert "quadratic_sort" in names
        assert len(names) == len(ALGORITHM_PATTERNS)

    def test_improvement_factor_format(self):
        """Each improvement_factor should contain an arrow (→)."""
        for name, entry in ALGORITHM_PATTERNS.items():
            assert "→" in entry["improvement_factor"], (
                f"Pattern '{name}' improvement_factor missing arrow: "
                f"{entry['improvement_factor']}"
            )


# ── Brute Force Detector Tests ──────────────────────────────────────────────

class TestBruteForceDetector:
    """Tests for BruteForceDetector pattern matching."""

    def test_detects_naive_two_sum(self, time_analyzer, detector):
        """Naive two-sum (nested loops) should be detected as brute-force."""
        ast_results = time_analyzer.analyze(NAIVE_TWO_SUM)
        detected = detector.detect(ast_results, NAIVE_TWO_SUM)

        assert len(detected) == 1
        d = detected[0]
        assert d.function_name == "two_sum"
        assert d.pattern_name == "nested_loop_two_sum"
        assert d.match_score >= 0.5
        assert d.pattern_entry["brute_force_complexity"] == "O(n²)"
        assert d.pattern_entry["optimal_complexity"] == "O(n)"

    def test_skips_optimal_two_sum(self, time_analyzer, detector):
        """Optimal two-sum (hash map) should NOT be flagged."""
        ast_results = time_analyzer.analyze(OPTIMAL_TWO_SUM)
        detected = detector.detect(ast_results, OPTIMAL_TWO_SUM)

        # Should be empty — hash map solution is already optimal
        assert len(detected) == 0

    def test_detects_bubble_sort(self, time_analyzer, detector):
        """Bubble sort should be detected as a quadratic sort pattern."""
        ast_results = time_analyzer.analyze(BUBBLE_SORT)
        detected = detector.detect(ast_results, BUBBLE_SORT)

        assert len(detected) == 1
        d = detected[0]
        assert d.function_name == "bubble_sort"
        # Should match quadratic_sort or nested_loop pattern
        assert "sort" in d.pattern_name or "nested" in d.pattern_name
        assert d.match_score >= 0.5

    def test_skips_binary_search(self, time_analyzer, detector):
        """Binary search (O(log n)) should NOT be flagged."""
        ast_results = time_analyzer.analyze(BINARY_SEARCH)
        detected = detector.detect(ast_results, BINARY_SEARCH)

        assert len(detected) == 0

    def test_skips_constant_function(self, time_analyzer, detector):
        """O(1) function should NOT be flagged."""
        ast_results = time_analyzer.analyze(SIMPLE_GETTER)
        detected = detector.detect(ast_results, SIMPLE_GETTER)

        assert len(detected) == 0

    def test_skips_optimal_duplicate_check(self, time_analyzer, detector):
        """Optimal duplicate check (set) should NOT be flagged."""
        ast_results = time_analyzer.analyze(CONTAINS_DUPLICATE_OPTIMAL)
        detected = detector.detect(ast_results, CONTAINS_DUPLICATE_OPTIMAL)

        assert len(detected) == 0

    def test_detects_naive_duplicate_check(self, time_analyzer, detector):
        """Naive duplicate check (nested loops) should be detected."""
        ast_results = time_analyzer.analyze(NAIVE_DUPLICATE_CHECK)
        detected = detector.detect(ast_results, NAIVE_DUPLICATE_CHECK)

        assert len(detected) == 1
        d = detected[0]
        assert d.function_name == "find_duplicate"
        assert d.match_score >= 0.5

    def test_empty_results(self, detector):
        """Empty AST results should return empty detected list."""
        detected = detector.detect([], "")
        assert detected == []

    def test_mixed_functions_only_flags_brute_force(self, time_analyzer, detector):
        """In mixed code, only brute-force functions should be flagged."""
        ast_results = time_analyzer.analyze(MIXED_FUNCTIONS)
        detected = detector.detect(ast_results, MIXED_FUNCTIONS)

        # Only naive_pair_sum should be flagged
        flagged_names = {d.function_name for d in detected}
        assert "naive_pair_sum" in flagged_names
        assert "optimal_lookup" not in flagged_names
        assert "get_value" not in flagged_names

    def test_detected_pattern_has_function_code(self, time_analyzer, detector):
        """Detected patterns should include the function's source code."""
        ast_results = time_analyzer.analyze(NAIVE_TWO_SUM)
        detected = detector.detect(ast_results, NAIVE_TWO_SUM)

        assert len(detected) == 1
        assert "for i in range" in detected[0].function_code
        assert "for j in range" in detected[0].function_code


# ── OptimizationOpportunity Model Tests ─────────────────────────────────────

class TestOptimizationOpportunityModel:
    """Tests for the OptimizationOpportunity Pydantic model."""

    def test_valid_opportunity(self):
        """Should create a valid OptimizationOpportunity."""
        opp = OptimizationOpportunity(
            pattern_name="nested_loop_two_sum",
            current_complexity="O(n²)",
            optimal_complexity="O(n)",
            improvement_factor="O(n²) → O(n)",
            suggested_approach="Hash map (single pass)",
            explanation="The nested loop checks all pairs in O(n²). A hash map reduces this to O(n). Each element is processed once.",
            example_code="def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        if target - num in seen:\n            return [seen[target-num], i]\n        seen[num] = i\n    return []",
            function_name="two_sum",
            line_start=1,
            line_end=6,
        )
        assert opp.pattern_name == "nested_loop_two_sum"
        assert opp.improvement_factor == "O(n²) → O(n)"
        assert opp.example_code is not None
        assert "seen" in opp.example_code

    def test_opportunity_without_example_code(self):
        """Should allow example_code to be None (LLM failure fallback)."""
        opp = OptimizationOpportunity(
            pattern_name="quadratic_sort",
            current_complexity="O(n²)",
            optimal_complexity="O(n log n)",
            improvement_factor="O(n²) → O(n log n)",
            suggested_approach="Merge sort / Timsort",
            explanation="The bubble sort is O(n²). Use built-in sorted() for O(n log n).",
            example_code=None,
            function_name="bubble_sort",
            line_start=1,
            line_end=7,
        )
        assert opp.example_code is None
        assert opp.suggested_approach == "Merge sort / Timsort"

    def test_opportunity_serialisation(self):
        """Should serialise to dict correctly."""
        opp = OptimizationOpportunity(
            pattern_name="nested_loop_two_sum",
            current_complexity="O(n²)",
            optimal_complexity="O(n)",
            improvement_factor="O(n²) → O(n)",
            suggested_approach="Hash map",
            explanation="Use a hash map.",
            example_code="pass",
            function_name="two_sum",
            line_start=1,
            line_end=6,
        )
        data = opp.model_dump()
        assert data["pattern_name"] == "nested_loop_two_sum"
        assert data["example_code"] == "pass"
        assert data["function_name"] == "two_sum"


# ── Deliverable Verification ────────────────────────────────────────────────

class TestDeliverable:
    """
    Verify the Day 14 deliverable: submitting a naive O(n²) two-sum
    implementation triggers an OptimizationOpportunity with the correct
    pattern, complexity comparison, and improvement factor.
    """

    def test_naive_two_sum_triggers_optimization(self, time_analyzer, detector):
        """
        End-to-end: naive two-sum should:
            - Be detected as O(n²) by AST
            - Match 'nested_loop_two_sum' pattern
            - Have improvement_factor 'O(n²) → O(n)'
            - Have suggested_approach mentioning 'hash map'
        """
        # Step 1: AST analysis
        ast_results = time_analyzer.analyze(NAIVE_TWO_SUM)
        assert len(ast_results) == 1
        assert ast_results[0].time_complexity == "O(n²)"

        # Step 2: Brute-force detection
        detected = detector.detect(ast_results, NAIVE_TWO_SUM)
        assert len(detected) == 1

        d = detected[0]
        assert d.pattern_name == "nested_loop_two_sum"
        assert d.pattern_entry["improvement_factor"] == "O(n²) → O(n)"
        assert "hash map" in d.pattern_entry["optimal_approach"].lower()
        assert d.function_code.strip().startswith("def two_sum")
