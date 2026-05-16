"""
CoDude — Per-Function Complexity Annotator Tests (Day 13)

Tests Big-O detection for common algorithmic patterns:
    1. Bubble sort            → O(n²) time, O(1) space
    2. Binary search          → O(log n) time, O(1) space
    3. Hash map lookup        → O(n) time (loop), O(n) space
    4. Simple getter (O(1))   → O(1) time, O(1) space
    5. Nested 3-deep loops    → O(n³) time
    6. Recursive function     → O(n) time, O(n) space (stack)
    7. Merge sort (d&c)       → O(n log n) time
    8. Contains duplicate     → O(n) time, O(n) space
    9. Matrix creation        → O(n²) space
    10. Multiple functions    → one result per function

All tests use ASTComplexityAnalyzer and SpaceAnalyzer directly
(no LLM calls needed) to verify the AST pattern matching logic.
"""

import ast
import pytest

from app.services.complexity.ast_complexity import ASTComplexityAnalyzer
from app.services.complexity.space_analyzer import SpaceAnalyzer


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def time_analyzer():
    """Create an ASTComplexityAnalyzer instance."""
    return ASTComplexityAnalyzer()


@pytest.fixture
def space_analyzer():
    """Create a SpaceAnalyzer instance."""
    return SpaceAnalyzer()


# ── Test Code Samples ───────────────────────────────────────────────────────

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

HASH_MAP_LOOKUP = """\
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

SIMPLE_GETTER = """\
def get_first(items):
    return items[0]
"""

TRIPLE_NESTED = """\
def matrix_multiply(a, b, n):
    result = []
    for i in range(n):
        row = []
        for j in range(n):
            total = 0
            for k in range(n):
                total += a[i][k] * b[k][j]
            row.append(total)
        result.append(row)
    return result
"""

RECURSIVE_LINEAR = """\
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

MERGE_SORT = """\
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)
"""

CONTAINS_DUPLICATE = """\
def contains_duplicate(nums):
    seen = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
"""

MATRIX_CREATION = """\
def create_matrix(n):
    return [[0 for _ in range(n)] for _ in range(n)]
"""

MULTIPLE_FUNCTIONS = """\
def linear_search(arr, target):
    for item in arr:
        if item == target:
            return True
    return False

def constant_op(x, y):
    return x + y

def quadratic(arr):
    for i in arr:
        for j in arr:
            print(i, j)
"""

LOOP_WITH_DICT_ONLY = """\
def count_frequency(items):
    freq = {}
    for item in items:
        freq[item] = freq.get(item, 0) + 1
    return freq
"""


# ── Time Complexity Tests ───────────────────────────────────────────────────

class TestASTTimeComplexity:
    """Tests for ASTComplexityAnalyzer time complexity detection."""

    def test_bubble_sort_is_quadratic(self, time_analyzer):
        """Bubble sort should be detected as O(n²) with high confidence."""
        results = time_analyzer.analyze(BUBBLE_SORT)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "bubble_sort"
        assert r.time_complexity == "O(n²)"
        assert r.confidence == "high"
        assert r.max_loop_depth == 2

    def test_binary_search_is_logarithmic(self, time_analyzer):
        """Binary search should be detected as O(log n) with high confidence."""
        results = time_analyzer.analyze(BINARY_SEARCH)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "binary_search"
        assert r.time_complexity == "O(log n)"
        assert r.confidence == "high"
        assert r.has_binary_search_pattern is True

    def test_hash_map_is_linear(self, time_analyzer):
        """Hash map lookup in a loop should be O(n), not O(n²)."""
        results = time_analyzer.analyze(HASH_MAP_LOOKUP)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "two_sum"
        assert r.time_complexity == "O(n)"
        assert r.confidence == "high"
        assert r.has_hash_lookup_in_loop is True

    def test_simple_getter_is_constant(self, time_analyzer):
        """A function with no loops/recursion should be O(1)."""
        results = time_analyzer.analyze(SIMPLE_GETTER)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "get_first"
        assert r.time_complexity == "O(1)"
        assert r.confidence == "high"

    def test_triple_nested_is_cubic(self, time_analyzer):
        """Three nested loops should be detected as O(n³)."""
        results = time_analyzer.analyze(TRIPLE_NESTED)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "matrix_multiply"
        assert r.time_complexity == "O(n³)"
        assert r.confidence == "high"
        assert r.max_loop_depth == 3

    def test_linear_recursion(self, time_analyzer):
        """Simple recursion without loops should be O(n) with medium confidence."""
        results = time_analyzer.analyze(RECURSIVE_LINEAR)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "factorial"
        assert r.time_complexity == "O(n)"
        assert r.confidence == "medium"
        assert r.has_recursion is True

    def test_merge_sort_divide_conquer(self, time_analyzer):
        """Recursive function with halving should be O(n log n)."""
        results = time_analyzer.analyze(MERGE_SORT)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "merge_sort"
        assert r.time_complexity == "O(n log n)"
        assert r.confidence == "medium"
        assert r.recursive_with_halving is True

    def test_contains_duplicate_is_linear(self, time_analyzer):
        """Set lookup in loop should be O(n)."""
        results = time_analyzer.analyze(CONTAINS_DUPLICATE)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "contains_duplicate"
        assert r.time_complexity == "O(n)"
        assert r.confidence == "high"

    def test_multiple_functions_analyzed(self, time_analyzer):
        """Multiple functions should each get their own result."""
        results = time_analyzer.analyze(MULTIPLE_FUNCTIONS)
        assert len(results) == 3

        names = {r.function_name for r in results}
        assert names == {"linear_search", "constant_op", "quadratic"}

        by_name = {r.function_name: r for r in results}
        assert by_name["linear_search"].time_complexity == "O(n)"
        assert by_name["constant_op"].time_complexity == "O(1)"
        assert by_name["quadratic"].time_complexity == "O(n²)"

    def test_dict_frequency_counter_is_linear(self, time_analyzer):
        """Loop with dict[key] access should be O(n), not O(n²)."""
        results = time_analyzer.analyze(LOOP_WITH_DICT_ONLY)
        assert len(results) == 1
        r = results[0]
        assert r.function_name == "count_frequency"
        assert r.time_complexity == "O(n)"
        assert r.confidence == "high"

    def test_syntax_error_returns_empty(self, time_analyzer):
        """Invalid code should return empty list, not crash."""
        results = time_analyzer.analyze("def broken(:\n    pass")
        assert results == []

    def test_line_numbers_captured(self, time_analyzer):
        """Line start and end should be captured correctly."""
        results = time_analyzer.analyze(BUBBLE_SORT)
        r = results[0]
        assert r.line_start == 1
        assert r.line_end >= 6  # function spans multiple lines


# ── Space Complexity Tests ──────────────────────────────────────────────────

class TestSpaceComplexity:
    """Tests for SpaceAnalyzer space complexity detection."""

    def test_bubble_sort_space_constant(self, space_analyzer):
        """Bubble sort (in-place) should have O(1) space."""
        tree = ast.parse(BUBBLE_SORT)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(1)"

    def test_binary_search_space_constant(self, space_analyzer):
        """Binary search (iterative) should have O(1) space."""
        tree = ast.parse(BINARY_SEARCH)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(1)"

    def test_hash_map_space_linear(self, space_analyzer):
        """Building a dict in a loop should have O(n) space."""
        tree = ast.parse(HASH_MAP_LOOKUP)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(n)"

    def test_set_space_linear(self, space_analyzer):
        """Building a set should have O(n) space."""
        tree = ast.parse(CONTAINS_DUPLICATE)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(n)"

    def test_recursive_space_linear(self, space_analyzer):
        """Recursive function should have O(n) stack space."""
        tree = ast.parse(RECURSIVE_LINEAR)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(n)"
        assert result.has_recursion is True

    def test_matrix_creation_space_quadratic(self, space_analyzer):
        """2D list comprehension should have O(n²) space."""
        tree = ast.parse(MATRIX_CREATION)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(n²)"
        assert result.has_nested_list is True

    def test_simple_getter_space_constant(self, space_analyzer):
        """Simple getter with no allocations should have O(1) space."""
        tree = ast.parse(SIMPLE_GETTER)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(1)"

    def test_analyze_code_all_functions(self, space_analyzer):
        """analyze_code should return results for all functions."""
        results = space_analyzer.analyze_code(MULTIPLE_FUNCTIONS)
        assert len(results) == 3
        assert "linear_search" in results
        assert "constant_op" in results
        assert "quadratic" in results

    def test_dict_frequency_space_linear(self, space_analyzer):
        """Dict built inside loop should have O(n) space."""
        tree = ast.parse(LOOP_WITH_DICT_ONLY)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        result = space_analyzer.analyze_function(func)
        assert result.space_complexity == "O(n)"


# ── Integration: Deliverable Verification ───────────────────────────────────

class TestDeliverable:
    """
    Verify the Day 13 deliverable: bubble sort returns FunctionComplexity
    with time_complexity: O(n²), space_complexity: O(1), and reasoning.
    """

    def test_bubble_sort_full_analysis(self, time_analyzer, space_analyzer):
        """
        End-to-end: bubble sort should produce:
            - time_complexity: O(n²)
            - space_complexity: O(1)
            - confidence: high
            - reasoning includes explanation
        """
        time_results = time_analyzer.analyze(BUBBLE_SORT)
        assert len(time_results) == 1

        time_r = time_results[0]
        assert time_r.function_name == "bubble_sort"
        assert time_r.time_complexity == "O(n²)"
        assert time_r.confidence == "high"

        space_results = space_analyzer.analyze_code(BUBBLE_SORT)
        space_r = space_results["bubble_sort"]
        assert space_r.space_complexity == "O(1)"

        # Verify reasoning is present and meaningful
        assert len(time_r.reasoning) > 20
        assert "bubble_sort" in time_r.reasoning
        assert len(space_r.reasoning) > 20

    def test_binary_search_full_analysis(self, time_analyzer, space_analyzer):
        """Binary search: O(log n) time, O(1) space."""
        time_results = time_analyzer.analyze(BINARY_SEARCH)
        time_r = time_results[0]
        assert time_r.time_complexity == "O(log n)"

        space_results = space_analyzer.analyze_code(BINARY_SEARCH)
        space_r = space_results["binary_search"]
        assert space_r.space_complexity == "O(1)"

    def test_hash_map_full_analysis(self, time_analyzer, space_analyzer):
        """Hash map: O(n) time, O(n) space."""
        time_results = time_analyzer.analyze(HASH_MAP_LOOKUP)
        time_r = time_results[0]
        assert time_r.time_complexity == "O(n)"

        space_results = space_analyzer.analyze_code(HASH_MAP_LOOKUP)
        space_r = space_results["two_sum"]
        assert space_r.space_complexity == "O(n)"
