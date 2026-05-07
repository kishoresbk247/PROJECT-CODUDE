"""
CoDude — Structured Output Schema for LLM Responses

Defines the Pydantic model that LangChain's .with_structured_output()
uses to constrain the LLM's response format.

This schema mirrors the CodeReviewResponse shape from app.models.review,
but is defined separately because LangChain's structured output requires
models with specific Field descriptions that map to the function-calling
schema sent to OpenAI.

The LLM will ALWAYS return data matching this shape — no manual JSON
parsing, no regex extraction, no retry-on-parse-failure loops.

How it works under the hood:
    1. LangChain converts this Pydantic model into an OpenAI function schema
    2. The LLM is forced to call that function with valid arguments
    3. LangChain parses the function call arguments back into this model
    4. We get a validated Pydantic instance, guaranteed to match the schema
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


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
        ..., description="Explanation of why the code has this complexity"
    )
    brute_force_alternative: Optional[str] = Field(
        None,
        description="Alternative brute-force approach complexity for comparison",
    )


class CodeReviewSchema(BaseModel):
    """
    Top-level structured output schema for the code review LLM chain.

    This is the schema passed to llm.with_structured_output() so the
    LLM is forced to respond in exactly this shape.
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
