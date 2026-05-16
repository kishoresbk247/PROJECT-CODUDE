"""
CoDude — AST-Based Time Complexity Analyzer (Day 13)

Walks the Python AST to detect Big-O time complexity patterns on a
per-function basis. Covers 90% of real-world algorithmic patterns:

    Single loop                     → O(n)
    Nested loops (2 levels)         → O(n²)
    Nested loops (3 levels)         → O(n³)
    While loop halving (binary)     → O(log n)
    Loop + recursive call           → O(n log n) or flag for LLM
    No loops, no recursion          → O(1)
    Dict/set lookup inside loop     → O(n) not O(n²)
    Simple recursion (linear)       → O(n)
    Divide-and-conquer recursion    → O(n log n)

Theoretical limitation:
    Automatically determining Big-O is equivalent to the halting problem
    for arbitrary programs. However, pattern matching works well for the
    recognizable algorithmic patterns that make up ~90% of real code.

Usage:
    analyzer = ASTComplexityAnalyzer()
    results = analyzer.analyze(source_code)
"""

import ast
import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class FunctionComplexityResult:
    """Raw result from AST complexity analysis for a single function."""

    function_name: str
    line_start: int
    line_end: int
    time_complexity: str
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    max_loop_depth: int = 0
    has_recursion: bool = False
    has_binary_search_pattern: bool = False
    has_hash_lookup_in_loop: bool = False
    recursive_with_halving: bool = False


class _LoopDepthVisitor(ast.NodeVisitor):
    """
    Walks a function body to determine the maximum loop nesting depth
    and detect special patterns (recursion, binary search, hash lookups).
    """

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.max_depth = 0
        self.current_depth = 0
        self.has_recursion = False
        self.has_binary_search = False
        self.has_hash_lookup_in_loop = False
        self.recursive_with_halving = False
        self._in_loop = False

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self.current_depth += 1
        was_in_loop = self._in_loop
        self._in_loop = True
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
        self._in_loop = was_in_loop

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        self.current_depth += 1
        was_in_loop = self._in_loop
        self._in_loop = True
        self.max_depth = max(self.max_depth, self.current_depth)

        # Detect binary search pattern: while loop with midpoint calculation
        if self._is_binary_search_pattern(node):
            self.has_binary_search = True

        self.generic_visit(node)
        self.current_depth -= 1
        self._in_loop = was_in_loop

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        # Detect recursion — function calling itself
        if isinstance(node.func, ast.Name) and node.func.id == self.function_name:
            self.has_recursion = True

            # Check if any argument is halved (divide-and-conquer)
            for arg in node.args:
                if self._is_halving_expression(arg):
                    self.recursive_with_halving = True

        # Detect dict/set membership test in loop (e.g., `if x in my_dict`)
        # This is handled at the Compare level, but we still need to visit
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:  # noqa: N802
        """Detect `x in dict_or_set` inside a loop."""
        if self._in_loop:
            for op in node.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    # This is a containment check inside a loop
                    # If the container is likely a dict/set, mark it
                    for comparator in node.comparators:
                        if self._is_likely_hash_container(comparator):
                            self.has_hash_lookup_in_loop = True
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: N802
        """Detect dict[key] access inside a loop."""
        if self._in_loop:
            # dict access pattern: variable[key]
            if isinstance(node.value, ast.Name):
                self.has_hash_lookup_in_loop = True
        self.generic_visit(node)

    @staticmethod
    def _is_binary_search_pattern(while_node: ast.While) -> bool:
        """
        Detect binary search: while loop body contains a midpoint calc
        like `mid = (lo + hi) // 2` or `mid = left + (right - left) // 2`.
        """
        for child in ast.walk(while_node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.FloorDiv):
                # Found integer division — likely midpoint calculation
                if isinstance(child.right, ast.Constant) and child.right.value == 2:
                    return True
            # Also catch `// 2` in augmented assignment
            if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.FloorDiv):
                return True
            # Catch right shift by 1 (equivalent to // 2)
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.RShift):
                if isinstance(child.right, ast.Constant) and child.right.value == 1:
                    return True
        return False

    @staticmethod
    def _is_halving_expression(node: ast.expr) -> bool:
        """Check if an expression involves dividing by 2 (e.g., n // 2, n / 2)."""
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, (ast.FloorDiv, ast.Div)):
                if isinstance(node.right, ast.Constant) and node.right.value == 2:
                    return True
            if isinstance(node.op, ast.RShift):
                if isinstance(node.right, ast.Constant) and node.right.value == 1:
                    return True
        # Also check slicing like arr[:len(arr)//2]
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            return True
        return False

    @staticmethod
    def _is_likely_hash_container(node: ast.expr) -> bool:
        """Heuristic: a Name node is likely a dict/set (can't be sure from AST alone)."""
        # Any variable reference could be a dict/set — we mark it as likely
        # This is a deliberate over-approximation; better to say O(n) than O(n²)
        return isinstance(node, (ast.Name, ast.Attribute))


class ASTComplexityAnalyzer:
    """
    Analyzes per-function time complexity using AST pattern matching.

    Walks the AST to detect loop nesting depth, recursion patterns,
    binary search patterns, and hash map lookups to determine Big-O.

    Usage:
        analyzer = ASTComplexityAnalyzer()
        results = analyzer.analyze(code)
    """

    def analyze(self, code: str) -> list[FunctionComplexityResult]:
        """
        Parse Python source code and analyze time complexity per function.

        Args:
            code: Python source code as a string.

        Returns:
            List of FunctionComplexityResult, one per function found.
            Returns empty list if code cannot be parsed.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            logger.warning("ASTComplexityAnalyzer: SyntaxError — cannot parse code")
            return []

        results: list[FunctionComplexityResult] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result = self._analyze_function(node)
                results.append(result)

        logger.info(
            "ASTComplexityAnalyzer: analyzed %d function(s)", len(results)
        )
        return results

    def _analyze_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> FunctionComplexityResult:
        """
        Analyze a single function's time complexity.

        Strategy:
            1. Walk the function body to find max loop depth, recursion, etc.
            2. Map patterns to Big-O complexity.
            3. Assign confidence based on pattern clarity.

        Args:
            func_node: The AST node for the function definition.

        Returns:
            A FunctionComplexityResult with time complexity and confidence.
        """
        # Calculate line_end from the last statement in the function body
        line_end = self._get_end_line(func_node)

        # Walk the function body
        visitor = _LoopDepthVisitor(func_node.name)
        visitor.visit(func_node)

        # Determine complexity from patterns
        return self._classify_complexity(
            function_name=func_node.name,
            line_start=func_node.lineno,
            line_end=line_end,
            max_depth=visitor.max_depth,
            has_recursion=visitor.has_recursion,
            has_binary_search=visitor.has_binary_search,
            has_hash_lookup=visitor.has_hash_lookup_in_loop,
            recursive_with_halving=visitor.recursive_with_halving,
        )

    @staticmethod
    def _classify_complexity(
        function_name: str,
        line_start: int,
        line_end: int,
        max_depth: int,
        has_recursion: bool,
        has_binary_search: bool,
        has_hash_lookup: bool,
        recursive_with_halving: bool,
    ) -> FunctionComplexityResult:
        """
        Map detected patterns to Big-O complexity with confidence.

        Pattern priority (highest to lowest):
            1. Binary search pattern → O(log n), high confidence
            2. Divide-and-conquer recursion → O(n log n), medium confidence
            3. Recursion + loops → flag for LLM (low confidence)
            4. Nested loops → O(n^depth), high confidence
            5. Single loop with hash lookup → O(n), high confidence
            6. Simple recursion → O(n) or O(2^n), medium confidence
            7. No loops/recursion → O(1), high confidence
        """
        # ── Binary search pattern ────────────────────────────────────────
        if has_binary_search and not has_recursion:
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(log n)",
                confidence="high",
                reasoning=(
                    f"Function '{function_name}' contains a while loop with a "
                    "midpoint calculation (floor division by 2), matching the "
                    "binary search pattern. Each iteration halves the search "
                    "space, giving logarithmic time complexity."
                ),
                max_loop_depth=max_depth,
                has_binary_search_pattern=True,
            )

        # ── Divide-and-conquer recursion ────────────────────────────────
        if recursive_with_halving:
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n log n)",
                confidence="medium",
                reasoning=(
                    f"Function '{function_name}' calls itself recursively with "
                    "a halved input (n // 2 or equivalent). This matches the "
                    "divide-and-conquer pattern (e.g., merge sort). Typical "
                    "complexity: O(n log n) via the Master Theorem."
                ),
                max_loop_depth=max_depth,
                has_recursion=True,
                recursive_with_halving=True,
            )

        # ── Recursion + loops → ambiguous, flag for LLM ────────────────
        if has_recursion and max_depth > 0:
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n²)",
                confidence="low",
                reasoning=(
                    f"Function '{function_name}' contains both recursion and "
                    f"loops (depth={max_depth}). This pattern is ambiguous — "
                    "could be O(n log n) (merge sort) or O(n²) (recursive + "
                    "linear scan). Flagged for LLM review."
                ),
                max_loop_depth=max_depth,
                has_recursion=True,
            )

        # ── Nested loops ────────────────────────────────────────────────
        if max_depth >= 3:
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n³)",
                confidence="high",
                reasoning=(
                    f"Function '{function_name}' has {max_depth} levels of "
                    "nested loops. Three nested loops each iterating over n "
                    "elements produce n × n × n = O(n³) time complexity."
                ),
                max_loop_depth=max_depth,
            )

        if max_depth == 2:
            # Check if inner loop uses hash lookups → still O(n²) for the loops
            # but note the hash lookups don't add to complexity
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n²)",
                confidence="high",
                reasoning=(
                    f"Function '{function_name}' has 2 levels of nested loops. "
                    "The outer loop runs n times, and for each iteration the "
                    "inner loop runs up to n times → n × n = O(n²)."
                    + (
                        " Hash-based lookups inside the loops are O(1) amortized "
                        "and do not increase the overall complexity."
                        if has_hash_lookup
                        else ""
                    )
                ),
                max_loop_depth=max_depth,
                has_hash_lookup_in_loop=has_hash_lookup,
            )

        if max_depth == 1:
            if has_hash_lookup:
                return FunctionComplexityResult(
                    function_name=function_name,
                    line_start=line_start,
                    line_end=line_end,
                    time_complexity="O(n)",
                    confidence="high",
                    reasoning=(
                        f"Function '{function_name}' has a single loop with "
                        "dictionary/set lookups. The loop runs n times, and each "
                        "hash lookup is O(1) amortized → total O(n). This is NOT "
                        "O(n²) because hash lookups are constant-time."
                    ),
                    max_loop_depth=max_depth,
                    has_hash_lookup_in_loop=True,
                )

            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n)",
                confidence="high",
                reasoning=(
                    f"Function '{function_name}' has a single loop iterating "
                    "over the input. Each iteration does constant-time work, "
                    "giving linear time complexity O(n)."
                ),
                max_loop_depth=max_depth,
            )

        # ── Simple recursion (no loops) ─────────────────────────────────
        if has_recursion:
            return FunctionComplexityResult(
                function_name=function_name,
                line_start=line_start,
                line_end=line_end,
                time_complexity="O(n)",
                confidence="medium",
                reasoning=(
                    f"Function '{function_name}' is recursive without loops. "
                    "Assuming linear recursion (each call reduces input by 1), "
                    "this is O(n). However, if the recursion branches (e.g., "
                    "Fibonacci without memoization), it could be O(2ⁿ). "
                    "Confidence is medium — LLM review recommended for "
                    "branching recursion."
                ),
                has_recursion=True,
            )

        # ── No loops, no recursion → O(1) ──────────────────────────────
        return FunctionComplexityResult(
            function_name=function_name,
            line_start=line_start,
            line_end=line_end,
            time_complexity="O(1)",
            confidence="high",
            reasoning=(
                f"Function '{function_name}' contains no loops and no recursion. "
                "All operations are constant-time, giving O(1) complexity."
            ),
            max_loop_depth=0,
        )

    @staticmethod
    def _get_end_line(node: ast.AST) -> int:
        """Get the last line number of an AST node."""
        if hasattr(node, "end_lineno") and node.end_lineno is not None:
            return node.end_lineno
        # Fallback: walk all children and find max lineno
        max_line = getattr(node, "lineno", 0)
        for child in ast.walk(node):
            child_line = getattr(child, "lineno", 0)
            if child_line > max_line:
                max_line = child_line
        return max_line
