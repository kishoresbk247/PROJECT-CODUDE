"""
CoDude — Per-Function Complexity Annotator Package (Day 15)

Provides per-function Big-O time and space complexity analysis using a
hybrid approach:

    1. AST pattern matching (fast, deterministic, zero cost)
    2. Space complexity detection (data structure analysis)
    3. LLM fallback for low-confidence functions (selective, cost-aware)
    4. Brute-force pattern detection (Day 14)
    5. Targeted LLM solution generation for detected patterns (Day 14)
    6. Visualization data for frontend charting (Day 15)
    7. LLM-generated narrative summary (Day 15)

Components:
    - ASTComplexityAnalyzer:  Detects time complexity from loop/recursion patterns
    - SpaceAnalyzer:          Detects space complexity from data structure usage
    - BruteForceDetector:     Cross-references AST results with pattern library
    - SolutionGenerator:      Generates optimised code via targeted LLM prompts
    - ComplexityVisualizer:   Converts analysis to frontend-ready chart data
    - ComplexityService:      Orchestrator — AST first, LLM for low-confidence only

All analyzers return FunctionComplexity objects with confidence levels.
Brute-force detection returns OptimizationOpportunity objects.
Visualization returns ComplexityVisualization with numeric scores.
"""

from app.services.complexity.ast_complexity import ASTComplexityAnalyzer
from app.services.complexity.brute_force_detector import BruteForceDetector
from app.services.complexity.complexity_visualizer import ComplexityVisualizer
from app.services.complexity.space_analyzer import SpaceAnalyzer
from app.services.complexity.solution_generator import SolutionGenerator
from app.services.complexity.complexity_service import ComplexityService

__all__ = [
    "ASTComplexityAnalyzer",
    "BruteForceDetector",
    "ComplexityVisualizer",
    "SpaceAnalyzer",
    "SolutionGenerator",
    "ComplexityService",
]
