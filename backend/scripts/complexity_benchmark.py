"""
CoDude — Complexity Benchmark Script (Day 15)

Validates the accuracy of the AST-based complexity detection by running
it against 5 well-known algorithm implementations with known Big-O
complexities.

Test cases:
    1. Quicksort          → Expected: O(n log n) time, O(log n) space
    2. Linear search      → Expected: O(n) time, O(1) space
    3. Fibonacci (naive)  → Expected: O(2ⁿ) time, O(n) space
    4. Fibonacci (memo)   → Expected: O(n) time, O(n) space
    5. Two-sum (hash)     → Expected: O(n) time, O(n) space

Target: 80%+ correct detection accuracy.

Usage:
    cd backend
    python -m scripts.complexity_benchmark
"""

import sys
import os
import io

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.complexity.ast_complexity import ASTComplexityAnalyzer
from app.services.complexity.space_analyzer import SpaceAnalyzer
from app.services.complexity.complexity_visualizer import complexity_to_score


# ── Test Algorithm Implementations ───────────────────────────────────────────

ALGORITHMS = {
    "quicksort": {
        "code": '''\
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
''',
        "expected_time": "O(n log n)",
        "expected_space": "O(n)",
        "expected_time_score": 4,
    },
    "linear_search": {
        "code": '''\
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
''',
        "expected_time": "O(n)",
        "expected_space": "O(1)",
        "expected_time_score": 3,
    },
    "fibonacci_naive": {
        "code": '''\
def fibonacci_naive(n):
    if n <= 1:
        return n
    return fibonacci_naive(n - 1) + fibonacci_naive(n - 2)
''',
        "expected_time": "O(2ⁿ)",
        "expected_space": "O(n)",
        "expected_time_score": 6,
    },
    "fibonacci_memoized": {
        "code": '''\
def fibonacci_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n - 1, memo) + fibonacci_memo(n - 2, memo)
    return memo[n]
''',
        "expected_time": "O(n)",
        "expected_space": "O(n)",
        "expected_time_score": 3,
    },
    "two_sum_hash": {
        "code": '''\
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
''',
        "expected_time": "O(n)",
        "expected_space": "O(n)",
        "expected_time_score": 3,
    },
}


def run_benchmark():
    """
    Run the complexity benchmark against all test algorithms.

    For each algorithm:
        1. Run AST time complexity analysis
        2. Run space complexity analysis
        3. Convert detected complexity to numeric score
        4. Compare detected vs expected
        5. Print results table

    Returns:
        Tuple of (correct_count, total_count, accuracy_percentage)
    """
    analyzer = ASTComplexityAnalyzer()
    space_analyzer = SpaceAnalyzer()

    print("=" * 80)
    print("CoDude Complexity Detection Benchmark (Day 15)")
    print("=" * 80)
    print()

    # Table header
    header = (
        f"{'Algorithm':<22} "
        f"{'Expected Time':<15} "
        f"{'Detected Time':<15} "
        f"{'Expected Space':<15} "
        f"{'Detected Space':<15} "
        f"{'Score':<8} "
        f"{'Match':<6}"
    )
    print(header)
    print("-" * len(header))

    correct_time = 0
    correct_space = 0
    total = len(ALGORITHMS)

    results = []

    for name, algo in ALGORITHMS.items():
        code = algo["code"]
        expected_time = algo["expected_time"]
        expected_space = algo["expected_space"]
        expected_score = algo["expected_time_score"]

        # Run AST time analysis
        time_results = analyzer.analyze(code)
        if time_results:
            detected_time = time_results[0].time_complexity
        else:
            detected_time = "N/A"

        # Run space analysis
        space_results = space_analyzer.analyze_code(code)
        if space_results:
            first_func = list(space_results.values())[0]
            detected_space = first_func.space_complexity
        else:
            detected_space = "O(1)"

        # Convert to scores for comparison
        detected_score = complexity_to_score(detected_time) if detected_time != "N/A" else 0

        # Check accuracy (score-based comparison for flexibility)
        time_match = detected_score == expected_score
        space_score_detected = complexity_to_score(detected_space)
        space_score_expected = complexity_to_score(expected_space)
        space_match = space_score_detected == space_score_expected

        if time_match:
            correct_time += 1
        if space_match:
            correct_space += 1

        match_symbol = "PASS" if time_match else "FAIL"

        print(
            f"{name:<22} "
            f"{expected_time:<15} "
            f"{detected_time:<15} "
            f"{expected_space:<15} "
            f"{detected_space:<15} "
            f"{detected_score}/{expected_score:<6} "
            f"{match_symbol:<6}"
        )

        results.append({
            "name": name,
            "expected_time": expected_time,
            "detected_time": detected_time,
            "expected_space": expected_space,
            "detected_space": detected_space,
            "time_match": time_match,
            "space_match": space_match,
        })

    print("-" * len(header))

    # Summary
    time_accuracy = (correct_time / total) * 100
    space_accuracy = (correct_space / total) * 100
    overall_accuracy = ((correct_time + correct_space) / (total * 2)) * 100

    print()
    print(f"Time Complexity Accuracy:   {correct_time}/{total} ({time_accuracy:.0f}%)")
    print(f"Space Complexity Accuracy:  {correct_space}/{total} ({space_accuracy:.0f}%)")
    print(f"Overall Accuracy:           {correct_time + correct_space}/{total * 2} ({overall_accuracy:.0f}%)")
    print()

    # Score mapping reference
    print("Score mapping: O(1)=1, O(log n)=2, O(n)=3, O(n log n)=4, O(n²)=5, O(2ⁿ)=6")
    print()

    target_met = time_accuracy >= 80
    if target_met:
        print(f"PASS: {time_accuracy:.0f}% time detection accuracy (target: 80%+)")
    else:
        print(f"FAIL: {time_accuracy:.0f}% time detection accuracy (target: 80%+)")

    print("=" * 80)

    return correct_time, total, time_accuracy, results


if __name__ == "__main__":
    correct, total, accuracy, results = run_benchmark()
    sys.exit(0 if accuracy >= 80 else 1)
