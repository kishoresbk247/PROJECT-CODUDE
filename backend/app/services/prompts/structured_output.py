"""
CoDude — Structured Output Schemas for LLM Responses (Day 05 Update)

Defines Pydantic models used by LangChain's .with_structured_output() to
constrain the LLM's response format.

Day 05 changes:
    - Added BugDetectionSchema (for bug-only chain)
    - Added SecurityReviewSchema (for security-only chain)
    - Added ComplexityAnalysisSchema (for complexity-only chain)
    - Kept CodeReviewSchema for backward compatibility

The LLM will ALWAYS return data matching these shapes — no manual JSON
parsing, no regex extraction, no retry-on-parse-failure loops.

How it works under the hood:
    1. LangChain converts the Pydantic model into an OpenAI function schema
    2. The LLM is forced to call that function with valid arguments
    3. LangChain parses the function call arguments back into the model
    4. We get a validated Pydantic instance, guaranteed to match the schema
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Shared Sub-Schemas ───────────────────────────────────────────────────────

class BugFindingSchema(BaseModel):
    """Schema for a single bug finding in the LLM response."""

    line: Optional[int] = Field(None, description="Line number where the bug occurs")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Severity level of the bug"
    )
    message: str = Field(..., description="Description of the bug found")
    suggestion: str = Field(..., description="Suggested fix for the bug")


class SecurityFindingSchema(BaseModel):
    """Schema for a single security vulnerability in the LLM response."""

    line: Optional[int] = Field(
        None, description="Line number where the vulnerability occurs"
    )
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Severity level of the vulnerability"
    )
    message: str = Field(..., description="Description of the security vulnerability")
    suggestion: str = Field(..., description="Suggested remediation")
    owasp_category: str = Field(
        ...,
        description="OWASP Top 10 category (e.g. 'A03:2021 – Injection')",
    )


class ComplexitySchema(BaseModel):
    """Schema for complexity analysis in the LLM response."""

    time_complexity: str = Field(
        ..., description="Time complexity in Big-O notation (e.g. 'O(n²)')"
    )
    space_complexity: str = Field(
        ..., description="Space complexity in Big-O notation (e.g. 'O(n)')"
    )
    explanation: str = Field(
        ..., description="Step-by-step explanation of the complexity derivation"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggested optimal alternative if the current solution is suboptimal, null if already optimal",
    )


# ── Specialized Schemas (Day 05 — one per parallel chain) ────────────────────

class BugDetectionSchema(BaseModel):
    """
    Structured output for the bug-detection-only chain.

    The LLM returns a list of bugs. If no bugs are found, the list is empty.
    """

    bugs: list[BugFindingSchema] = Field(
        default_factory=list, description="List of bugs found in the code"
    )


class SecurityReviewSchema(BaseModel):
    """
    Structured output for the security-review-only chain.

    The LLM returns a list of security findings. If no vulnerabilities
    are found, the list is empty.
    """

    security: list[SecurityFindingSchema] = Field(
        default_factory=list,
        description="List of security vulnerabilities found",
    )


class ComplexityAnalysisSchema(BaseModel):
    """
    Structured output for the complexity-analysis-only chain.

    The LLM returns a single complexity analysis object.
    """

    time_complexity: str = Field(
        ..., description="Time complexity in Big-O notation (e.g. 'O(n²)')"
    )
    space_complexity: str = Field(
        ..., description="Space complexity in Big-O notation (e.g. 'O(n)')"
    )
    explanation: str = Field(
        ..., description="Step-by-step explanation of the complexity derivation"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggested optimal alternative if suboptimal, null if already optimal",
    )


# ── Legacy Combined Schema (backward compatible with Day 04) ────────────────

class CodeReviewSchema(BaseModel):
    """
    Top-level structured output schema for the combined code review chain.

    Kept for backward compatibility. Day 05's ReviewService uses the
    specialized schemas above and merges results.
    """

    bugs: list[BugFindingSchema] = Field(
        default_factory=list, description="List of bugs found in the code"
    )
    security: list[SecurityFindingSchema] = Field(
        default_factory=list,
        description="List of security vulnerabilities found",
    )
    complexity: Optional[ComplexitySchema] = Field(
        None, description="Complexity analysis of the code"
    )
    summary: str = Field(
        ..., description="Concise human-readable summary of the review"
    )
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Code quality score from 0 (terrible) to 100 (perfect)",
    )
