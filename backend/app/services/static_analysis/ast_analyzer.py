"""
CoDude — AST-Based Bug Detector (Day 07)

Uses Python's built-in `ast` module to detect common bugs by walking the
Abstract Syntax Tree.  Unlike regex, AST parsing understands code *structure*:
it knows that `def foo(x=[])` has a mutable default because it parsed the
grammar — not because it found square brackets in text.

Detected patterns:
    1. Mutable default arguments   — list, dict, or set as function defaults
    2. Bare except clauses         — `except:` without specifying an exception type
    3. Comparison to None with ==  — should use `is None` instead of `== None`
    4. Unused loop variables       — for-loop target never referenced in the body

Each finding is returned as a BugFinding with source="static".
"""

import ast
from dataclasses import dataclass, field


@dataclass
class BugFinding:
    """A single bug detected by static analysis."""

    line: int
    severity: str
    message: str
    suggestion: str
    source: str = "static"


class _NameCollector(ast.NodeVisitor):
    """Collects all ast.Name nodes (variable references) in a subtree."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        self.names.add(node.id)
        self.generic_visit(node)


class ASTAnalyzer:
    """
    Static bug detector powered by Python's ast module.

    Usage:
        analyzer = ASTAnalyzer()
        findings = analyzer.analyze("def foo(x=[]):\\n    pass")
    """

    def analyze(self, code: str) -> list[BugFinding]:
        """
        Parse the given Python source and detect common bugs.

        Args:
            code: Python source code as a string.

        Returns:
            A list of BugFinding objects, one per detected issue.
            Returns an empty list if the code cannot be parsed.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [
                BugFinding(
                    line=1,
                    severity="critical",
                    message="SyntaxError: code could not be parsed",
                    suggestion="Fix the syntax error before submitting for review.",
                )
            ]

        findings: list[BugFinding] = []
        findings.extend(self._check_mutable_defaults(tree))
        findings.extend(self._check_bare_excepts(tree))
        findings.extend(self._check_none_comparison(tree))
        findings.extend(self._check_unused_loop_vars(tree))
        return findings

    # ── Detection Rules ──────────────────────────────────────────────────

    @staticmethod
    def _check_mutable_defaults(tree: ast.Module) -> list[BugFinding]:
        """
        Detect mutable default arguments in function definitions.

        Mutable defaults (list, dict, set) are shared across all calls,
        leading to subtle bugs where mutations persist between invocations.

        Example:
            def foo(x=[]):        # ← BUG: shared list across calls
                x.append(1)
                return x
        """
        findings: list[BugFinding] = []
        mutable_types = (ast.List, ast.Dict, ast.Set)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default is not None and isinstance(default, mutable_types):
                        type_name = type(default).__name__.lower()
                        findings.append(
                            BugFinding(
                                line=node.lineno,
                                severity="high",
                                message=(
                                    f"Mutable default argument ({type_name}) in "
                                    f"function '{node.name}'. Mutable defaults are "
                                    f"shared across all calls."
                                ),
                                suggestion=(
                                    f"Use `None` as default and initialise inside "
                                    f"the function body: `if param is None: param = "
                                    f"{type_name}()`"
                                ),
                            )
                        )
        return findings

    @staticmethod
    def _check_bare_excepts(tree: ast.Module) -> list[BugFinding]:
        """
        Detect bare `except:` clauses that catch all exceptions.

        Bare excepts catch SystemExit, KeyboardInterrupt, GeneratorExit —
        making it impossible to Ctrl+C out of a program and hiding real errors.

        Example:
            try:
                risky()
            except:            # ← BUG: catches everything
                pass
        """
        findings: list[BugFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(
                    BugFinding(
                        line=node.lineno,
                        severity="medium",
                        message=(
                            "Bare `except:` clause catches all exceptions, "
                            "including SystemExit and KeyboardInterrupt."
                        ),
                        suggestion=(
                            "Specify the exception type: `except Exception:` "
                            "or a more specific type like `except ValueError:`."
                        ),
                    )
                )
        return findings

    @staticmethod
    def _check_none_comparison(tree: ast.Module) -> list[BugFinding]:
        """
        Detect comparisons to None using == instead of `is`.

        `== None` invokes __eq__, which can be overridden. `is None` checks
        identity, which is the Pythonic and correct way to test for None.

        Example:
            if x == None:      # ← BUG: should be `x is None`
                ...
        """
        findings: list[BugFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for op, comparator in zip(node.ops, node.comparators):
                    if (
                        isinstance(op, ast.Eq)
                        and isinstance(comparator, ast.Constant)
                        and comparator.value is None
                    ):
                        findings.append(
                            BugFinding(
                                line=node.lineno,
                                severity="low",
                                message=(
                                    "Comparison to `None` using `==`. This invokes "
                                    "`__eq__`, which can be overridden and may produce "
                                    "unexpected results."
                                ),
                                suggestion="Use `is None` instead of `== None`.",
                            )
                        )
        return findings

    @staticmethod
    def _check_unused_loop_vars(tree: ast.Module) -> list[BugFinding]:
        """
        Detect for-loop variables that are never used in the loop body.

        Convention: `_` is the accepted throwaway name and is excluded.

        Example:
            for item in items:     # ← WARNING: 'item' never used
                print("hello")
        """
        findings: list[BugFinding] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                var_name = node.target.id
                # Skip conventional throwaway variable
                if var_name == "_":
                    continue

                # Collect all Name references in the loop body
                collector = _NameCollector()
                for child in node.body:
                    collector.visit(child)
                # Also check the else clause
                for child in node.orelse:
                    collector.visit(child)

                if var_name not in collector.names:
                    findings.append(
                        BugFinding(
                            line=node.lineno,
                            severity="low",
                            message=(
                                f"Loop variable '{var_name}' is never used "
                                f"in the loop body."
                            ),
                            suggestion=(
                                f"If the variable is intentionally unused, "
                                f"rename it to `_` to signal intent."
                            ),
                        )
                    )
        return findings
