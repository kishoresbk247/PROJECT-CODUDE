"""Quick verification that all Day 15 imports work and scores are correct."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.review import ComplexityVisualization, ComplexityResult
from app.services.complexity.complexity_visualizer import ComplexityVisualizer, complexity_to_score
from app.services.complexity.summary_generator import generate_summary

print("All imports OK")

# Test score mapping
tests = {
    "O(1)": 1,
    "O(log n)": 2,
    "O(n)": 3,
    "O(n log n)": 4,
    "O(n^2)": 5,
    "O(2^n)": 6,
}

all_pass = True
for complexity, expected in tests.items():
    actual = complexity_to_score(complexity)
    status = "PASS" if actual == expected else "FAIL"
    print(f"  {complexity:>12} -> {actual} (expected {expected}) [{status}]")
    if actual != expected:
        all_pass = False

if all_pass:
    print("\nAll score mapping tests PASSED!")
else:
    print("\nSome tests FAILED!")
    sys.exit(1)
