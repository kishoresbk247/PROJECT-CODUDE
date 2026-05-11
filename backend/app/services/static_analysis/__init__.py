"""
CoDude — Static Analysis Package (Day 08)

Multi-language static analysis for code review:

    AST-based (Python only):
        - ASTAnalyzer:        Detects common bugs (mutable defaults, bare excepts, etc.)
        - ComplexityChecker:  Computes cyclomatic complexity per function
        - StyleChecker:       Enforces naming conventions, function length, docstrings

    Regex-based (JavaScript, Java):
        - PatternMatcher:     Applies language-specific regex patterns
        - LanguageDetector:   Auto-identifies language from code content / filename

All analyzers return list[BugFinding] and run without any LLM API call.
"""

from app.services.static_analysis.ast_analyzer import ASTAnalyzer
from app.services.static_analysis.complexity_checker import ComplexityChecker
from app.services.static_analysis.language_detector import LanguageDetector
from app.services.static_analysis.pattern_matcher import PatternMatcher
from app.services.static_analysis.style_checker import StyleChecker

__all__ = [
    "ASTAnalyzer",
    "ComplexityChecker",
    "LanguageDetector",
    "PatternMatcher",
    "StyleChecker",
]
