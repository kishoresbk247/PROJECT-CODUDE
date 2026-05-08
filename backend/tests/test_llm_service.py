"""
CoDude — LLM Service & Review Service Tests (Day 05 Update)

Tests the LangChain integration WITHOUT hitting the real OpenAI API.
Uses unittest.mock to patch ChatOpenAI so tests are fast, free, and
deterministic.

Day 05 updates:
    - Updated ReviewService tests for the new parallel chain architecture
    - Added tests for _merge_results, _compute_score, _synthesise_summary
    - Tests use the new specialized schemas (BugDetectionSchema, etc.)

Key testing strategy:
    - Mock the LLM's .ainvoke() to return a fake AIMessage
    - Mock .with_structured_output() to return a runnable that produces
      fake specialized schemas
    - Verify the full chain executes without errors
    - Verify the ReviewService correctly merges parallel chain outputs
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_service import LLMService
from app.services.prompts.structured_output import (
    BugDetectionSchema,
    BugFindingSchema,
    CodeReviewSchema,
    ComplexityAnalysisSchema,
    ComplexitySchema,
    SecurityFindingSchema,
    SecurityReviewSchema,
)
from app.services.review_service import ReviewService
from app.models.review import CodeReviewRequest


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_bug_result() -> BugDetectionSchema:
    """Create a mock bug detection result."""
    return BugDetectionSchema(
        bugs=[
            BugFindingSchema(
                line=5,
                severity="medium",
                message="Unused variable 'temp'.",
                suggestion="Remove the unused variable.",
            ),
        ]
    )


@pytest.fixture
def mock_security_result() -> SecurityReviewSchema:
    """Create a mock security review result."""
    return SecurityReviewSchema(
        security=[
            SecurityFindingSchema(
                line=10,
                severity="critical",
                message="SQL injection via string interpolation.",
                suggestion="Use parameterized queries.",
                owasp_category="A03:2021 – Injection",
            ),
        ]
    )


@pytest.fixture
def mock_complexity_result() -> ComplexityAnalysisSchema:
    """Create a mock complexity analysis result."""
    return ComplexityAnalysisSchema(
        time_complexity="O(n²)",
        space_complexity="O(1)",
        explanation="Nested loop over the input array.",
        suggestion="Use a hash map to reduce to O(n).",
    )


@pytest.fixture
def mock_complexity_result_optimal() -> ComplexityAnalysisSchema:
    """Create a mock complexity result for optimal code."""
    return ComplexityAnalysisSchema(
        time_complexity="O(n)",
        space_complexity="O(n)",
        explanation="Single pass with hash set lookups.",
        suggestion=None,
    )


@pytest.fixture
def mock_schema() -> CodeReviewSchema:
    """Create a realistic mock CodeReviewSchema for legacy tests."""
    return CodeReviewSchema(
        bugs=[
            BugFindingSchema(
                line=5,
                severity="medium",
                message="Unused variable 'temp'.",
                suggestion="Remove the unused variable.",
            ),
        ],
        security=[],
        complexity=ComplexitySchema(
            time_complexity="O(n²)",
            space_complexity="O(1)",
            explanation="Nested loop over the input array.",
            suggestion=None,
        ),
        summary="Code has minor issues. One unused variable found.",
        overall_score=78,
    )


# ── LLMService Tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestLLMService:
    """Tests for the base LLMService class."""

    @patch("app.services.llm_service.ChatOpenAI")
    async def test_invoke_returns_string(self, mock_chat_cls: MagicMock) -> None:
        """invoke() should return the text content from the LLM response."""
        # Arrange: mock the ChatOpenAI instance
        mock_llm_instance = MagicMock()
        mock_chat_cls.return_value = mock_llm_instance

        # Mock ainvoke to return a fake AIMessage
        fake_message = MagicMock()
        fake_message.content = "This code looks good overall."
        mock_llm_instance.ainvoke = AsyncMock(return_value=fake_message)

        # Act
        service = LLMService()
        result = await service.invoke("Review this code")

        # Assert
        assert result == "This code looks good overall."
        mock_llm_instance.ainvoke.assert_called_once_with("Review this code")

    @patch("app.services.llm_service.ChatOpenAI")
    async def test_with_structured_output_calls_llm(
        self, mock_chat_cls: MagicMock
    ) -> None:
        """with_structured_output() should delegate to the LLM's method."""
        mock_llm_instance = MagicMock()
        mock_chat_cls.return_value = mock_llm_instance

        service = LLMService()
        service.with_structured_output(CodeReviewSchema)

        mock_llm_instance.with_structured_output.assert_called_once_with(
            CodeReviewSchema
        )


# ── ReviewService Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestReviewService:
    """Tests for the ReviewService with parallel specialized chains (Day 05)."""

    def test_merge_results_maps_correctly(
        self,
        mock_bug_result: BugDetectionSchema,
        mock_security_result: SecurityReviewSchema,
        mock_complexity_result: ComplexityAnalysisSchema,
    ) -> None:
        """
        _merge_results should correctly map all three chain outputs
        into a single CodeReviewResponse.
        """
        response = ReviewService._merge_results(
            mock_bug_result, mock_security_result, mock_complexity_result
        )

        # Verify bugs are mapped
        assert len(response.bugs) == 1
        assert response.bugs[0].severity == "medium"
        assert response.bugs[0].line == 5

        # Verify security findings are mapped
        assert len(response.security) == 1
        assert response.security[0].severity == "critical"
        assert response.security[0].owasp_category == "A03:2021 – Injection"

        # Verify complexity is mapped
        assert response.complexity is not None
        assert response.complexity.time_complexity == "O(n²)"
        assert response.complexity.space_complexity == "O(1)"
        assert response.complexity.brute_force_alternative == "Use a hash map to reduce to O(n)."

    def test_merge_results_clean_code(
        self,
        mock_complexity_result_optimal: ComplexityAnalysisSchema,
    ) -> None:
        """_merge_results should handle clean code (no bugs, no security)."""
        bug_result = BugDetectionSchema(bugs=[])
        security_result = SecurityReviewSchema(security=[])

        response = ReviewService._merge_results(
            bug_result, security_result, mock_complexity_result_optimal
        )

        assert len(response.bugs) == 0
        assert len(response.security) == 0
        assert response.overall_score == 100
        assert "No bugs detected" in response.summary
        assert "No security vulnerabilities" in response.summary

    def test_compute_score_perfect(self) -> None:
        """Score should be 100 for code with no findings."""
        assert ReviewService._compute_score([], []) == 100

    def test_compute_score_critical_findings(
        self,
        mock_bug_result: BugDetectionSchema,
        mock_security_result: SecurityReviewSchema,
    ) -> None:
        """Score should decrease based on finding severity."""
        from app.models.review import BugFinding, SecurityFinding

        bugs = [
            BugFinding(line=5, severity="medium", message="test", suggestion="fix")
        ]
        security = [
            SecurityFinding(
                line=10, severity="critical", message="test",
                suggestion="fix", owasp_category="A03:2021"
            )
        ]

        score = ReviewService._compute_score(bugs, security)
        # 100 - 8 (medium) - 20 (critical) = 72
        assert score == 72

    def test_compute_score_minimum_is_zero(self) -> None:
        """Score should never go below 0."""
        from app.models.review import BugFinding

        many_bugs = [
            BugFinding(line=i, severity="critical", message="bug", suggestion="fix")
            for i in range(10)
        ]
        score = ReviewService._compute_score(many_bugs, [])
        assert score == 0

    def test_synthesise_summary_with_findings(
        self,
        mock_bug_result: BugDetectionSchema,
        mock_security_result: SecurityReviewSchema,
        mock_complexity_result: ComplexityAnalysisSchema,
    ) -> None:
        """Summary should mention bugs, security, and complexity."""
        response = ReviewService._merge_results(
            mock_bug_result, mock_security_result, mock_complexity_result
        )

        assert "1 bug(s)" in response.summary
        assert "1 security issue(s)" in response.summary
        assert "O(n²)" in response.summary
        assert "optimised alternative" in response.summary.lower()
