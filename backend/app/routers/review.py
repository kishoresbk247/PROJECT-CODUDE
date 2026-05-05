"""
CoDude — Review Router

Stub endpoints for the code review API.
Each endpoint returns realistic mock data so the frontend team and
integration tests can work against a stable contract while the AI
service layer is built out in later days.

Routes:
    POST /api/v1/review            — Full code review (bugs + security + complexity)
    POST /api/v1/review/bugs       — Bug detection only
    POST /api/v1/review/security   — Security analysis only
    POST /api/v1/review/complexity — Complexity analysis only
"""

from fastapi import APIRouter

from app.models.review import (
    BugFinding,
    CodeReviewRequest,
    CodeReviewResponse,
    ComplexityResult,
    SecurityFinding,
)

router = APIRouter(prefix="/api/v1", tags=["review"])


# ── Mock Data Generators ─────────────────────────────────────────────────────
# These will be replaced by real AI service calls in later days.


def _mock_bugs() -> list[BugFinding]:
    """Return a realistic list of mock bug findings."""
    return [
        BugFinding(
            line=10,
            severity="medium",
            message="Variable 'x' is defined but never used.",
            suggestion="Remove the unused variable or use it in the logic.",
        ),
        BugFinding(
            line=25,
            severity="high",
            message="Potential division by zero on line 25.",
            suggestion="Add a guard clause to check if the divisor is non-zero.",
        ),
    ]


def _mock_security() -> list[SecurityFinding]:
    """Return a realistic list of mock security findings."""
    return [
        SecurityFinding(
            line=42,
            severity="critical",
            message="User input is passed directly to SQL query without sanitisation.",
            suggestion="Use parameterised queries or an ORM to prevent SQL injection.",
            owasp_category="A03:2021 – Injection",
        ),
    ]


def _mock_complexity() -> ComplexityResult:
    """Return a mock complexity analysis result."""
    return ComplexityResult(
        time_complexity="O(n²)",
        space_complexity="O(n)",
        explanation=(
            "The nested loop iterates over all pairs, resulting in quadratic time. "
            "A hash-map approach could reduce this to O(n)."
        ),
        brute_force_alternative="O(n³) with a triple-nested loop.",
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/review",
    response_model=CodeReviewResponse,
    summary="Full code review",
    description="Analyses code for bugs, security vulnerabilities, and complexity.",
)
async def review_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """
    Full code review endpoint.

    Accepts source code and returns a comprehensive review including
    bug findings, security findings, complexity analysis, and an
    overall quality score.

    This is currently a STUB — returns mock data.
    Will be wired to the AI service in a later day.
    """
    return CodeReviewResponse(
        bugs=_mock_bugs(),
        security=_mock_security(),
        complexity=_mock_complexity(),
        summary=(
            f"Reviewed {len(request.code)} characters of {request.language} code. "
            f"Found 2 bugs, 1 security issue. Overall quality is moderate."
        ),
        overall_score=62,
    )


@router.post(
    "/review/bugs",
    response_model=list[BugFinding],
    summary="Bug detection only",
    description="Scans code for bugs and code-quality issues.",
)
async def review_bugs(request: CodeReviewRequest) -> list[BugFinding]:
    """
    Bug-only review endpoint.

    Returns a list of bug findings without security or complexity analysis.
    Useful when the client only needs a quick lint-style check.

    This is currently a STUB — returns mock data.
    """
    return _mock_bugs()


@router.post(
    "/review/security",
    response_model=list[SecurityFinding],
    summary="Security analysis only",
    description="Scans code for security vulnerabilities (OWASP-categorised).",
)
async def review_security(request: CodeReviewRequest) -> list[SecurityFinding]:
    """
    Security-only review endpoint.

    Returns a list of security findings categorised by OWASP Top 10.
    Useful for security-focused audits.

    This is currently a STUB — returns mock data.
    """
    return _mock_security()


@router.post(
    "/review/complexity",
    response_model=ComplexityResult,
    summary="Complexity analysis only",
    description="Analyses time and space complexity of the submitted code.",
)
async def review_complexity(request: CodeReviewRequest) -> ComplexityResult:
    """
    Complexity-only review endpoint.

    Returns Big-O time and space complexity analysis.
    Useful for algorithm optimisation workflows.

    This is currently a STUB — returns mock data.
    """
    return _mock_complexity()
