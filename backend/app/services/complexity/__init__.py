"""
CoDude — Per-Function Complexity Annotator Package (Day 13)

Provides per-function Big-O time and space complexity analysis using a
hybrid approach:

    1. AST pattern matching (fast, deterministic, zero cost)
    2. Space complexity detection (data structure analysis)
    3. LLM fallback for low-confidence functions (selective, cost-aware)

Components:
    - ASTComplexityAnalyzer:  Detects time complexity from loop/recursion patterns
    - SpaceAnalyzer:          Detects space complexity from data structure usage
    - ComplexityService:      Orchestrator — AST first, LLM for low-confidence only

All analyzers return FunctionComplexity objects with confidence levels.
"""

from app.services.complexity.ast_complexity import ASTComplexityAnalyzer
from app.services.complexity.space_analyzer import SpaceAnalyzer
from app.services.complexity.complexity_service import ComplexityService

__all__ = [
    "ASTComplexityAnalyzer",
    "SpaceAnalyzer",
    "ComplexityService",
]
