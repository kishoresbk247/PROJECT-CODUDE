"""
CoDude — Pydantic Models for Code Review

Defines the request/response schemas for all /api/v1/review endpoints.
Uses Pydantic v2 conventions (model_config = ConfigDict(...)) for
maximum performance — the Pydantic v2 core is compiled in Rust and
is 5–50x faster than the v1 Python implementation.

Models:
    - CodeReviewRequest:   What the client sends (code + metadata)
    - BugFinding:          A single bug detected in the code
    - SecurityFinding:     A security vulnerability (extends BugFinding shape)
    - ComplexityResult:    Big-O analysis of the submitted code
    - CodeReviewResponse:  Aggregated results returned to the client
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request Model ────────────────────────────────────────────────────────────

class CodeReviewRequest(BaseModel):
    """
    Payload sent by the client to request a code review.

    Attributes:
        code:      The source code to analyse.
        language:  Programming language (e.g. "python", "javascript").
        filename:  Optional original filename for context in reports.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "code": "def add(a, b):\n    return a + b",
                    "language": "python",
                    "filename": "utils.py",
                }
            ]
        }
    )

    code: str = Field(..., min_length=1, description="Source code to review")
    language: str = Field(
        ...,
        min_length=1,
        description=(
            'Programming language (e.g. "python", "javascript", "java"). '
            'Use "auto" for automatic detection from code content or filename.'
        ),
    )
    filename: Optional[str] = Field(
        None, description="Original filename (optional, used in reports and auto-detection)"
    )


# ── Finding Models ───────────────────────────────────────────────────────────

class BugFinding(BaseModel):
    """
    Represents a single bug or code-quality issue found during review.

    Attributes:
        line:       Line number where the bug occurs (None if not localised).
        severity:   How critical the bug is.
        message:    Human-readable description of the issue.
        suggestion: Recommended fix or improvement.
    """

    model_config = ConfigDict(use_enum_values=True)

    line: Optional[int] = Field(None, description="Line number of the issue")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Issue severity level"
    )
    message: str = Field(..., description="Description of the bug")
    suggestion: str = Field(..., description="Suggested fix")
    source: Literal["static", "llm"] = Field(
        "llm", description="Detection source: 'static' (AST) or 'llm' (AI)"
    )


class SecurityFinding(BaseModel):
    """
    Represents a security vulnerability found during review.
    Same shape as BugFinding with an additional OWASP category.

    Attributes:
        line:            Line number where the vulnerability occurs.
        severity:        How critical the vulnerability is.
        message:         Human-readable description.
        suggestion:      Recommended remediation.
        owasp_category:  OWASP Top 10 category (e.g. "A01:2021 – Broken Access Control").
    """

    model_config = ConfigDict(use_enum_values=True)

    line: Optional[int] = Field(None, description="Line number of the issue")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Issue severity level"
    )
    message: str = Field(..., description="Description of the vulnerability")
    suggestion: str = Field(..., description="Suggested remediation")
    owasp_category: str = Field(
        ..., description="OWASP Top 10 category (e.g. A03:2021 – Injection)"
    )


class ComplexityResult(BaseModel):
    """
    Big-O complexity analysis of the submitted code.

    Attributes:
        time_complexity:          e.g. "O(n log n)"
        space_complexity:         e.g. "O(n)"
        explanation:              Why the code has this complexity.
        brute_force_alternative:  Optional note on a naïve approach for comparison.
    """

    time_complexity: str = Field(..., description="Time complexity (Big-O)")
    space_complexity: str = Field(..., description="Space complexity (Big-O)")
    explanation: str = Field(..., description="Explanation of the analysis")
    brute_force_alternative: Optional[str] = Field(
        None, description="Brute-force alternative for comparison"
    )


# ── Response Model ───────────────────────────────────────────────────────────

class CodeReviewResponse(BaseModel):
    """
    Aggregated review response returned to the client.

    Attributes:
        bugs:           List of bugs found.
        security:       List of security vulnerabilities found.
        complexity:     Complexity analysis result.
        summary:        Human-readable summary of the review.
        overall_score:  Quality score from 0 (terrible) to 100 (perfect).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "bugs": [],
                    "security": [],
                    "complexity": {
                        "time_complexity": "O(1)",
                        "space_complexity": "O(1)",
                        "explanation": "Simple addition.",
                        "brute_force_alternative": None,
                    },
                    "summary": "Clean code with no issues found.",
                    "overall_score": 95,
                }
            ]
        }
    )

    bugs: list[BugFinding] = Field(
        default_factory=list, description="List of bugs found"
    )
    security: list[SecurityFinding] = Field(
        default_factory=list, description="List of security vulnerabilities"
    )
    complexity: Optional[ComplexityResult] = Field(
        None, description="Complexity analysis result"
    )
    summary: str = Field(..., description="Human-readable review summary")
    overall_score: int = Field(
        ..., ge=0, le=100, description="Code quality score (0–100)"
    )
