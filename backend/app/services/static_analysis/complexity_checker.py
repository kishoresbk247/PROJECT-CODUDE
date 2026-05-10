"""
CoDude — Cyclomatic Complexity Checker (Day 07)

Walks the AST to compute cyclomatic complexity for every function in the
submitted Python code.

Cyclomatic complexity = 1 (base) + decision points.
Decision points counted:
    if, elif (via ast.If in orelse), for, while, except, and, or

Thresholds:
    ≤ 10  → "low"    (healthy)
    11–20 → "medium" (consider refactoring)
    > 20  → "high"   (refactor immediately)

Functions with complexity > 10 are flagged as BugFindings.
"""

import ast

from app.services.static_analysis.ast_analyzer import BugFinding


class _ComplexityVisitor(ast.NodeVisitor):
    """
    Counts decision points inside a single function body.

    Walks all child nodes and increments the complexity counter for
    each branching construct.
    """

    def __init__(self) -> None:
        self.complexity = 1  # Base complexity

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:  # noqa: N802
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:  # noqa: N802
        # Each `and`/`or` adds one decision point per additional operand
        # e.g., `a and b and c` has 2 decision points (2 `and` operators)
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class ComplexityChecker:
    """
    Computes cyclomatic complexity for each function and flags high-complexity ones.

    Usage:
        checker = ComplexityChecker()
        findings = checker.analyze("def big_func():\\n    ...")
    """

    HIGH_THRESHOLD = 10

    def analyze(self, code: str) -> list[BugFinding]:
        """
        Parse Python code and flag functions with cyclomatic complexity > 10.

        Args:
            code: Python source code as a string.

        Returns:
            A list of BugFinding objects for each high-complexity function.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Syntax errors are handled by ASTAnalyzer

        findings: list[BugFinding] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = _ComplexityVisitor()
                visitor.visit(node)
                complexity = visitor.complexity

                if complexity > self.HIGH_THRESHOLD:
                    level = "high" if complexity > 20 else "medium"
                    findings.append(
                        BugFinding(
                            line=node.lineno,
                            severity=level,
                            message=(
                                f"Function '{node.name}' has cyclomatic complexity "
                                f"of {complexity} (threshold: {self.HIGH_THRESHOLD}). "
                                f"High complexity makes code harder to test and maintain."
                            ),
                            suggestion=(
                                f"Refactor '{node.name}' by extracting helper functions, "
                                f"using early returns, or simplifying conditional logic."
                            ),
                        )
                    )

        return findings
