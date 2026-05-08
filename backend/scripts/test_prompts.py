"""
CoDude — Prompt Engineering Test Script (Day 05)

Sends three different code snippets through the ReviewService to demonstrate
the quality of the specialized prompt engineering:

    1. SQL injection vulnerability (should trigger security findings)
    2. O(n²) complexity code      (should trigger complexity suggestion)
    3. Clean, well-written code    (should return clean results)

Run from the backend directory:
    python -m scripts.test_prompts

This script uses the real ReviewService with live LLM calls (requires
OPENAI_API_KEY in .env). Temperature=0 ensures deterministic output.
"""

import asyncio
import json
import os
import sys
import time

# Fix Windows console encoding for emoji/unicode output
if sys.platform == "win32":
    os.system("")  # Enable ANSI escape codes on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure the app package is importable
sys.path.insert(0, ".")

from app.models.review import CodeReviewRequest
from app.services.review_service import ReviewService


# ── Test Snippets ────────────────────────────────────────────────────────────

# Snippet 1: SQL Injection vulnerability
SQL_INJECTION_CODE = """\
import sqlite3

def get_user_orders(username: str):
    \"\"\"Fetch all orders for a given username.\"\"\"
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    # Build query with user input
    query = f"SELECT * FROM orders WHERE customer = '{username}'"
    cursor.execute(query)
    results = cursor.fetchall()

    conn.close()
    return results

def delete_order(order_id):
    \"\"\"Delete an order by ID.\"\"\"
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = " + str(order_id))
    conn.commit()
    conn.close()
"""

# Snippet 2: O(n²) complexity — finding duplicates with nested loop
QUADRATIC_CODE = """\
def find_duplicates(arr):
    \"\"\"Find all duplicate elements in the array.\"\"\"
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates

def has_pair_with_sum(numbers, target):
    \"\"\"Check if any two numbers sum to target.\"\"\"
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] + numbers[j] == target:
                return True
    return False
"""

# Snippet 3: Clean, well-written Python code
CLEAN_CODE = """\
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    \"\"\"Immutable user value object.\"\"\"
    id: int
    name: str
    email: str


def find_user_by_email(users: list[User], email: str) -> Optional[User]:
    \"\"\"Find a user by email address.

    Args:
        users: List of User objects to search.
        email: Email address to find.

    Returns:
        The User with the matching email, or None if not found.
    \"\"\"
    email_lower = email.lower().strip()
    for user in users:
        if user.email.lower() == email_lower:
            return user
    return None


def compute_average(values: list[float]) -> float:
    \"\"\"Compute the arithmetic mean of a list of values.

    Args:
        values: Non-empty list of numeric values.

    Returns:
        The arithmetic mean.

    Raises:
        ValueError: If the list is empty.
    \"\"\"
    if not values:
        raise ValueError("Cannot compute average of an empty list")
    return sum(values) / len(values)
"""


# ── Display Helpers ──────────────────────────────────────────────────────────

DIVIDER = "=" * 80
SUB_DIVIDER = "-" * 60

COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
}


def color(text: str, c: str) -> str:
    """Wrap text in ANSI color codes."""
    return f"{COLORS.get(c, '')}{text}{COLORS['reset']}"


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{DIVIDER}")
    print(color(f"  {title}", "bold"))
    print(DIVIDER)


def print_findings(label: str, findings: list, emoji: str = "🔍") -> None:
    """Print a list of findings with formatting."""
    print(f"\n{emoji} {color(label, 'cyan')} ({len(findings)} found)")
    print(SUB_DIVIDER)

    if not findings:
        print(color("  ✅ None found — code is clean!", "green"))
        return

    for i, f in enumerate(findings, 1):
        finding_dict = f.model_dump() if hasattr(f, "model_dump") else f.__dict__
        severity = finding_dict.get("severity", "unknown")
        sev_color = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
        }.get(severity, "reset")

        print(f"\n  [{i}] {color(severity.upper(), sev_color)}"
              f" (line {finding_dict.get('line', '?')})")
        print(f"      Message:    {finding_dict.get('message', '')}")
        print(f"      Suggestion: {finding_dict.get('suggestion', '')}")
        if "owasp_category" in finding_dict:
            print(f"      OWASP:      {finding_dict['owasp_category']}")


def print_complexity(complexity) -> None:
    """Print complexity analysis with formatting."""
    print(f"\n📊 {color('Complexity Analysis', 'cyan')}")
    print(SUB_DIVIDER)

    if complexity is None:
        print(color("  No complexity analysis available.", "yellow"))
        return

    c = complexity.model_dump() if hasattr(complexity, "model_dump") else complexity.__dict__
    print(f"  Time:        {color(c['time_complexity'], 'magenta')}")
    print(f"  Space:       {color(c['space_complexity'], 'magenta')}")
    print(f"  Explanation: {c['explanation']}")
    if c.get("brute_force_alternative"):
        print(f"  💡 Suggestion: {color(c['brute_force_alternative'], 'green')}")


def print_result(response) -> None:
    """Print the full review response."""
    print_findings("Bug Findings", response.bugs, "🐛")
    print_findings("Security Findings", response.security, "🔒")
    print_complexity(response.complexity)

    print(f"\n📝 {color('Summary', 'cyan')}")
    print(SUB_DIVIDER)
    print(f"  {response.summary}")

    score = response.overall_score
    score_color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
    print(f"\n  ⭐ Overall Score: {color(str(score) + '/100', score_color)}")


# ── Test Runner ──────────────────────────────────────────────────────────────

async def run_test(
    service: ReviewService,
    name: str,
    code: str,
    language: str = "python",
) -> None:
    """Run a single test case and print results."""
    print_header(f"TEST: {name}")
    print(f"\n📄 {color('Input Code:', 'yellow')}")
    print(SUB_DIVIDER)
    for i, line in enumerate(code.strip().split("\n"), 1):
        print(f"  {i:3d} | {line}")

    request = CodeReviewRequest(code=code, language=language)

    start = time.perf_counter()
    try:
        response = await service.review(request)
        elapsed = time.perf_counter() - start

        print(f"\n⏱️  Completed in {color(f'{elapsed:.2f}s', 'green')}")
        print_result(response)

        # Also print raw JSON for inspection
        print(f"\n📋 {color('Raw JSON Output:', 'yellow')}")
        print(SUB_DIVIDER)
        raw = response.model_dump()
        print(json.dumps(raw, indent=2, default=str))

    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"\n❌ {color(f'FAILED after {elapsed:.2f}s: {exc}', 'red')}")
        import traceback
        traceback.print_exc()


async def main() -> None:
    """Run all three test cases."""
    print(color("\n🚀 CoDude — Day 05 Prompt Engineering Test Suite", "bold"))
    print(color("   Running 3 test snippets through parallel specialized chains\n", "cyan"))

    service = ReviewService()

    # Test 1: SQL injection code
    await run_test(
        service,
        "SQL Injection Vulnerability",
        SQL_INJECTION_CODE,
    )

    # Test 2: O(n²) complexity code
    await run_test(
        service,
        "O(n²) Quadratic Complexity",
        QUADRATIC_CODE,
    )

    # Test 3: Clean code
    await run_test(
        service,
        "Clean Well-Written Code",
        CLEAN_CODE,
    )

    print(f"\n{DIVIDER}")
    print(color("  ✅ All tests complete!", "green"))
    print(DIVIDER)


if __name__ == "__main__":
    asyncio.run(main())
