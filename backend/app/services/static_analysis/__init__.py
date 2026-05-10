"""
CoDude — Static Analysis Package (Day 07)

AST-based static bug detection for Python code. Provides three analyzers:

    - ASTAnalyzer:        Detects common bugs (mutable defaults, bare excepts, etc.)
    - ComplexityChecker:  Computes cyclomatic complexity per function
    - StyleChecker:       Enforces naming conventions, function length, docstrings

All analyzers return list[BugFinding] and run without any LLM API call.
"""

from app.services.static_analysis.ast_analyzer import ASTAnalyzer
from app.services.static_analysis.complexity_checker import ComplexityChecker
from app.services.static_analysis.style_checker import StyleChecker

__all__ = ["ASTAnalyzer", "ComplexityChecker", "StyleChecker"]
