"""
CoDude — Space Complexity Analyzer (Day 13)

Walks the Python AST to detect space complexity patterns per function:

    List comprehension over n items      → O(n)
    Dict/set built from n items          → O(n)
    Recursive function                   → O(depth) stack space
    In-place operations (no new allocs)  → O(1)
    Matrix/2D list creation              → O(n²)
    String concatenation in loop         → O(n) or O(n²)

The analyzer examines data structure allocations and recursive call
patterns to determine how much extra memory the function uses relative
to the input size.

Usage:
    analyzer = SpaceAnalyzer()
    space_complexity = analyzer.analyze_function(func_ast_node)
"""

import ast
import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class SpaceResult:
    """Space complexity analysis result for a single function."""

    space_complexity: str
    reasoning: str
    has_list_alloc: bool = False
    has_dict_alloc: bool = False
    has_set_alloc: bool = False
    has_recursion: bool = False
    has_nested_list: bool = False


class _SpacePatternVisitor(ast.NodeVisitor):
    """
    Walks a function body to detect space-consuming patterns:
    - List/dict/set creation (literals, comprehensions, constructor calls)
    - Recursive calls (stack space)
    - Nested data structures (2D lists)
    - String concatenation in loops
    """

    def __init__(self, function_name: str) -> None:
        self.function_name = function_name
        self.has_list_creation = False
        self.has_dict_creation = False
        self.has_set_creation = False
        self.has_recursion = False
        self.has_list_comprehension = False
        self.has_dict_comprehension = False
        self.has_set_comprehension = False
        self.has_nested_list = False
        self._in_loop = False
        self.has_append_in_loop = False
        self.has_string_concat_in_loop = False
        self.has_subscript_assign_in_loop = False

    def visit_ListComp(self, node: ast.ListComp) -> None:  # noqa: N802
        self.has_list_comprehension = True
        # Check for nested comprehension → 2D list → O(n²)
        # Case 1: the element is itself a ListComp: [row for row in [...]]
        if isinstance(node.elt, (ast.ListComp, ast.List)):
            self.has_nested_list = True
        # Case 2: the element is a BinOp like [0]*n (list multiplication)
        if isinstance(node.elt, ast.BinOp) and isinstance(node.elt.op, ast.Mult):
            self.has_nested_list = True
        # Case 3: the iterator is a ListComp
        for generator in node.generators:
            if isinstance(generator.iter, ast.ListComp):
                self.has_nested_list = True
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:  # noqa: N802
        self.has_dict_comprehension = True
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:  # noqa: N802
        self.has_set_comprehension = True
        self.generic_visit(node)

    def visit_List(self, node: ast.List) -> None:  # noqa: N802
        # Non-empty list literal
        if node.elts:
            self.has_list_creation = True
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:  # noqa: N802
        if node.keys:
            self.has_dict_creation = True
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> None:  # noqa: N802
        if node.elts:
            self.has_set_creation = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        # Detect recursion
        if isinstance(node.func, ast.Name):
            if node.func.id == self.function_name:
                self.has_recursion = True
            # Detect constructor calls: list(), dict(), set()
            elif node.func.id == "list":
                self.has_list_creation = True
            elif node.func.id == "dict":
                self.has_dict_creation = True
            elif node.func.id == "set":
                self.has_set_creation = True

        # Detect .append() in loop
        if self._in_loop and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("append", "extend", "insert"):
                self.has_append_in_loop = True

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        was_in_loop = self._in_loop
        self._in_loop = True
        self.generic_visit(node)
        self._in_loop = was_in_loop

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        was_in_loop = self._in_loop
        self._in_loop = True
        self.generic_visit(node)
        self._in_loop = was_in_loop

    def visit_AugAssign(self, node: ast.AugAssign) -> None:  # noqa: N802
        """Detect string += concatenation in loop."""
        if self._in_loop and isinstance(node.op, ast.Add):
            self.has_string_concat_in_loop = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        """Detect 2D list creation and dict subscript assignment in loops."""
        # Detect 2D list: result = [[0]*n for _ in range(n)]
        if isinstance(node.value, ast.ListComp):
            if isinstance(node.value.elt, (ast.List, ast.ListComp)):
                self.has_nested_list = True
            elif isinstance(node.value.elt, ast.BinOp) and isinstance(
                node.value.elt.op, ast.Mult
            ):
                self.has_nested_list = True

        # Detect dict[key] = value in loop (growing dict)
        if self._in_loop:
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    self.has_subscript_assign_in_loop = True

        self.generic_visit(node)


class SpaceAnalyzer:
    """
    Analyzes per-function space complexity using AST pattern matching.

    Detects memory allocation patterns (lists, dicts, sets, recursion)
    and classifies space complexity as O(1), O(n), O(n²), or O(depth).

    Usage:
        analyzer = SpaceAnalyzer()
        result = analyzer.analyze_function(func_node)
    """

    def analyze_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> SpaceResult:
        """
        Analyze space complexity for a single function.

        Args:
            func_node: The AST node for the function definition.

        Returns:
            SpaceResult with space complexity and reasoning.
        """
        visitor = _SpacePatternVisitor(func_node.name)
        visitor.visit(func_node)

        return self._classify_space(func_node.name, visitor)

    @staticmethod
    def _classify_space(function_name: str, v: _SpacePatternVisitor) -> SpaceResult:
        """
        Map detected space patterns to Big-O space complexity.

        Priority:
            1. Nested list creation → O(n²)
            2. List/dict/set comprehension or append in loop → O(n)
            3. Recursion without data allocation → O(n) stack space
            4. Small constant allocations → O(1)
        """
        # ── Nested data structures → O(n²) ──────────────────────────────
        if v.has_nested_list:
            return SpaceResult(
                space_complexity="O(n²)",
                reasoning=(
                    f"Function '{function_name}' creates a 2D data structure "
                    "(nested list). Each of the n rows contains n elements, "
                    "requiring n × n = O(n²) space."
                ),
                has_list_alloc=True,
                has_nested_list=True,
            )

        # ── Comprehension or growing collection → O(n) ──────────────────
        has_growing_collection = (
            v.has_list_comprehension
            or v.has_dict_comprehension
            or v.has_set_comprehension
            or v.has_append_in_loop
            or v.has_subscript_assign_in_loop
        )

        if has_growing_collection:
            alloc_type = "list"
            if v.has_dict_comprehension:
                alloc_type = "dictionary"
            elif v.has_set_comprehension:
                alloc_type = "set"

            return SpaceResult(
                space_complexity="O(n)",
                reasoning=(
                    f"Function '{function_name}' builds a {alloc_type} that "
                    "grows proportionally with the input size. Each input "
                    "element may contribute one entry to the collection, "
                    "requiring O(n) space."
                ),
                has_list_alloc=v.has_list_comprehension or v.has_append_in_loop,
                has_dict_alloc=v.has_dict_comprehension,
                has_set_alloc=v.has_set_comprehension,
            )

        # ── Dict/set creation from input → O(n) ─────────────────────────
        if v.has_dict_creation or v.has_set_creation:
            container = "dictionary" if v.has_dict_creation else "set"
            return SpaceResult(
                space_complexity="O(n)",
                reasoning=(
                    f"Function '{function_name}' creates a {container} which "
                    "may store up to n elements from the input. This requires "
                    "O(n) space in the worst case."
                ),
                has_dict_alloc=v.has_dict_creation,
                has_set_alloc=v.has_set_creation,
            )

        # ── Recursion → O(n) stack space (linear assumption) ────────────
        if v.has_recursion:
            return SpaceResult(
                space_complexity="O(n)",
                reasoning=(
                    f"Function '{function_name}' is recursive. Each recursive "
                    "call adds a stack frame. Assuming linear recursion depth "
                    "(proportional to input size), stack space is O(n). For "
                    "divide-and-conquer (halving), stack space is O(log n)."
                ),
                has_recursion=True,
            )

        # ── List creation (non-comprehension, small) → O(n) or O(1) ────
        if v.has_list_creation:
            return SpaceResult(
                space_complexity="O(n)",
                reasoning=(
                    f"Function '{function_name}' creates list(s). If the list "
                    "grows with the input, space is O(n). For small constant-"
                    "size lists, space is effectively O(1)."
                ),
                has_list_alloc=True,
            )

        # ── No significant allocations → O(1) ──────────────────────────
        return SpaceResult(
            space_complexity="O(1)",
            reasoning=(
                f"Function '{function_name}' performs in-place operations "
                "with no significant data structure allocations. Only a "
                "constant number of variables are used, giving O(1) space."
            ),
        )

    def analyze_code(self, code: str) -> dict[str, SpaceResult]:
        """
        Analyze space complexity for all functions in the code.

        Args:
            code: Python source code as a string.

        Returns:
            Dict mapping function_name → SpaceResult.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {}

        results: dict[str, SpaceResult] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                results[node.name] = self.analyze_function(node)

        return results
