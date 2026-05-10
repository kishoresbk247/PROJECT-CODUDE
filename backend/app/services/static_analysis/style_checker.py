"""
CoDude — Style Checker (Day 07)

Enforces Python style conventions using AST + regex:

    1. Function naming  — must be snake_case (PEP 8)
    2. Function length  — max 50 lines per function
    3. Module docstring — every file should have a docstring

Unlike pure-regex linters, we use the AST to find function definitions and
then apply regex only to the extracted name. This avoids false positives from
comments, strings, or decorators that happen to look like function names.
"""

import ast
import re

from app.services.static_analysis.ast_analyzer import BugFinding

# PEP 8 snake_case: lowercase letters, digits, underscores. Must start with
# a letter or underscore.  Dunder methods (__init__) are valid snake_case.
_SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class StyleChecker:
    """
    Checks Python code for style violations.

    Usage:
        checker = StyleChecker()
        findings = checker.analyze("def BadName():\\n    pass")
    """

    MAX_FUNCTION_LINES = 50

    def analyze(self, code: str) -> list[BugFinding]:
        """
        Parse Python code and check for style violations.

        Args:
            code: Python source code as a string.

        Returns:
            A list of BugFinding objects for each style violation.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Syntax errors are handled by ASTAnalyzer

        findings: list[BugFinding] = []
        findings.extend(self._check_function_names(tree))
        findings.extend(self._check_function_length(tree))
        findings.extend(self._check_module_docstring(tree))
        return findings

    # ── Style Rules ──────────────────────────────────────────────────────

    @staticmethod
    def _check_function_names(tree: ast.Module) -> list[BugFinding]:
        """
        Check that all function names follow snake_case convention.

        Dunder methods (__init__, __str__, etc.) are valid snake_case
        and pass this check.

        Example violation:
            def calculateTotal():   # ← camelCase
                ...
        """
        findings: list[BugFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not _SNAKE_CASE_RE.match(node.name):
                    findings.append(
                        BugFinding(
                            line=node.lineno,
                            severity="low",
                            message=(
                                f"Function '{node.name}' is not in snake_case. "
                                f"PEP 8 recommends lowercase_with_underscores "
                                f"for function names."
                            ),
                            suggestion=(
                                f"Rename to a snake_case equivalent, e.g. "
                                f"'{_to_snake_case(node.name)}'."
                            ),
                        )
                    )
        return findings

    @staticmethod
    def _check_function_length(tree: ast.Module) -> list[BugFinding]:
        """
        Flag functions exceeding 50 lines.

        Long functions are harder to understand, test, and maintain.
        The line count is measured from the first to last line of the
        function body (excluding the `def` line and decorators).
        """
        findings: list[BugFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function length from the function body
                if node.body:
                    first_line = node.body[0].lineno
                    last_line = _last_line(node)
                    func_length = last_line - first_line + 1

                    if func_length > StyleChecker.MAX_FUNCTION_LINES:
                        findings.append(
                            BugFinding(
                                line=node.lineno,
                                severity="medium",
                                message=(
                                    f"Function '{node.name}' is {func_length} lines "
                                    f"long (max: {StyleChecker.MAX_FUNCTION_LINES}). "
                                    f"Long functions are harder to test and maintain."
                                ),
                                suggestion=(
                                    f"Break '{node.name}' into smaller helper "
                                    f"functions, each handling one responsibility."
                                ),
                            )
                        )
        return findings

    @staticmethod
    def _check_module_docstring(tree: ast.Module) -> list[BugFinding]:
        """
        Check that the module has a docstring.

        A module docstring is an `ast.Expr` node containing an `ast.Constant`
        string as the very first statement in the module body.
        """
        findings: list[BugFinding] = []
        if not tree.body:
            return findings

        first_node = tree.body[0]
        has_docstring = (
            isinstance(first_node, ast.Expr)
            and isinstance(first_node.value, ast.Constant)
            and isinstance(first_node.value.value, str)
        )

        if not has_docstring:
            findings.append(
                BugFinding(
                    line=1,
                    severity="low",
                    message="Module is missing a docstring.",
                    suggestion=(
                        "Add a module-level docstring at the top of the file "
                        "explaining its purpose: `\"\"\"Module description.\"\"\"`"
                    ),
                )
            )
        return findings


# ── Helper Utilities ─────────────────────────────────────────────────────────


def _to_snake_case(name: str) -> str:
    """Convert a camelCase or PascalCase name to snake_case."""
    # Insert underscore before uppercase letters preceded by lowercase
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    # Insert underscore between consecutive uppercase and following lowercase
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)
    return result.lower()


def _last_line(node: ast.AST) -> int:
    """Recursively find the last line number in an AST subtree."""
    last = getattr(node, "lineno", 0)
    for child in ast.walk(node):
        child_line = getattr(child, "end_lineno", None) or getattr(
            child, "lineno", 0
        )
        if child_line > last:
            last = child_line
    return last
