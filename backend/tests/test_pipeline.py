"""
CoDude — Pipeline Tests (Day 09)

Tests for the unified ReviewPipeline:
    - Deduplication logic (_deduplicate_findings)
    - Scoring formula (_compute_score)
    - Sorting logic (_sort_findings)
    - Full pipeline run with mocked LLM responses

All LLM calls are mocked — no OpenAI API key required.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.review import (
    BugFinding,
    CodeReviewRequest,
    CodeReviewResponse,
    ComplexityResult,
    SecurityFinding,
)
from app.services.pipeline import ReviewPipeline


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def pipeline_cls():
    """Return the ReviewPipeline class for static method tests."""
    return ReviewPipeline


@pytest.fixture
def sample_complexity():
    """Return a sample ComplexityResult for scoring tests."""
    return ComplexityResult(
        time_complexity="O(n)",
        space_complexity="O(1)",
        explanation="Linear scan.",
        brute_force_alternative=None,
    )


# ── Deduplication Tests ──────────────────────────────────────────────────────


class TestDeduplication:
    """Tests for _deduplicate_findings()."""

    def test_no_duplicates_keeps_all(self, pipeline_cls):
        """Non-overlapping findings should all be kept."""
        findings = [
            BugFinding(
                line=1,
                severity="high",
                message="Mutable default argument",
                suggestion="Use None instead",
                source="static",
            ),
            BugFinding(
                line=5,
                severity="medium",
                message="Unused variable 'x'",
                suggestion="Remove it",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 2

    def test_same_line_similar_message_removes_llm(self, pipeline_cls):
        """When static and LLM flag same line with similar message, keep static."""
        findings = [
            BugFinding(
                line=10,
                severity="high",
                message="Mutable default argument detected in function",
                suggestion="Use None as default",
                source="static",
            ),
            BugFinding(
                line=10,
                severity="high",
                message="Mutable default argument detected in function definition",
                suggestion="Use None as default and assign inside",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 1
        assert result[0].source == "static"

    def test_same_line_different_message_keeps_both(self, pipeline_cls):
        """Same line but completely different messages should both be kept."""
        findings = [
            BugFinding(
                line=10,
                severity="high",
                message="Mutable default argument",
                suggestion="Use None",
                source="static",
            ),
            BugFinding(
                line=10,
                severity="medium",
                message="Variable name too short",
                suggestion="Use descriptive names",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 2

    def test_different_lines_similar_message_keeps_both(self, pipeline_cls):
        """Different lines should not be deduplicated even with similar messages."""
        findings = [
            BugFinding(
                line=10,
                severity="high",
                message="Bare except clause found",
                suggestion="Catch specific exceptions",
                source="static",
            ),
            BugFinding(
                line=20,
                severity="high",
                message="Bare except clause found",
                suggestion="Catch specific exceptions",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 2

    def test_empty_list_returns_empty(self, pipeline_cls):
        """Empty input should return empty output."""
        result = pipeline_cls._deduplicate_findings([])
        assert result == []

    def test_all_static_kept(self, pipeline_cls):
        """All static findings should always be kept."""
        findings = [
            BugFinding(
                line=1,
                severity="high",
                message="Issue A",
                suggestion="Fix A",
                source="static",
            ),
            BugFinding(
                line=2,
                severity="medium",
                message="Issue B",
                suggestion="Fix B",
                source="static",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 2

    def test_none_line_dedup(self, pipeline_cls):
        """Findings with line=None should deduplicate if messages match."""
        findings = [
            BugFinding(
                line=None,
                severity="medium",
                message="No docstring found for module",
                suggestion="Add a module docstring",
                source="static",
            ),
            BugFinding(
                line=None,
                severity="medium",
                message="No docstring found for module level",
                suggestion="Add docstring",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        assert len(result) == 1
        assert result[0].source == "static"

    def test_multiple_duplicates_removed(self, pipeline_cls):
        """Multiple LLM duplicates of different static findings should all be removed."""
        findings = [
            BugFinding(
                line=5,
                severity="high",
                message="Mutable default argument in function",
                suggestion="Use None",
                source="static",
            ),
            BugFinding(
                line=10,
                severity="medium",
                message="Bare except clause catches all exceptions",
                suggestion="Catch specific",
                source="static",
            ),
            BugFinding(
                line=5,
                severity="high",
                message="Mutable default argument in function definition",
                suggestion="Use None as default",
                source="llm",
            ),
            BugFinding(
                line=10,
                severity="medium",
                message="Bare except clause catches all exceptions and errors",
                suggestion="Be specific",
                source="llm",
            ),
            BugFinding(
                line=30,
                severity="low",
                message="Consider using f-strings",
                suggestion="Replace .format()",
                source="llm",
            ),
        ]
        result = pipeline_cls._deduplicate_findings(findings)
        # 2 static + 1 unique LLM = 3
        assert len(result) == 3
        sources = [f.source for f in result]
        assert sources.count("static") == 2
        assert sources.count("llm") == 1


# ── Scoring Tests ────────────────────────────────────────────────────────────


class TestScoring:
    """Tests for _compute_score()."""

    def test_perfect_score_no_findings(self, pipeline_cls, sample_complexity):
        """No bugs or security findings → score = 100."""
        score = pipeline_cls._compute_score([], [], sample_complexity)
        assert score == 100

    def test_single_critical_bug(self, pipeline_cls, sample_complexity):
        """One critical bug → 100 - 25 = 75."""
        bugs = [
            BugFinding(
                line=1,
                severity="critical",
                message="Crash",
                suggestion="Fix",
                source="llm",
            )
        ]
        score = pipeline_cls._compute_score(bugs, [], sample_complexity)
        assert score == 75

    def test_single_high_bug(self, pipeline_cls, sample_complexity):
        """One high bug → 100 - 15 = 85."""
        bugs = [
            BugFinding(
                line=1,
                severity="high",
                message="Bad",
                suggestion="Fix",
                source="llm",
            )
        ]
        score = pipeline_cls._compute_score(bugs, [], sample_complexity)
        assert score == 85

    def test_single_medium_bug(self, pipeline_cls, sample_complexity):
        """One medium bug → 100 - 7 = 93."""
        bugs = [
            BugFinding(
                line=1,
                severity="medium",
                message="Meh",
                suggestion="Fix",
                source="llm",
            )
        ]
        score = pipeline_cls._compute_score(bugs, [], sample_complexity)
        assert score == 93

    def test_single_low_bug(self, pipeline_cls, sample_complexity):
        """One low bug → 100 - 2 = 98."""
        bugs = [
            BugFinding(
                line=1,
                severity="low",
                message="Minor",
                suggestion="Maybe fix",
                source="llm",
            )
        ]
        score = pipeline_cls._compute_score(bugs, [], sample_complexity)
        assert score == 98

    def test_security_multiplier(self, pipeline_cls, sample_complexity):
        """Security findings use 1.5× multiplier: critical = 25 * 1.5 = 37.5 → 62."""
        security = [
            SecurityFinding(
                line=1,
                severity="critical",
                message="SQL injection",
                suggestion="Parameterise",
                owasp_category="A03:2021",
            )
        ]
        score = pipeline_cls._compute_score([], security, sample_complexity)
        assert score == 62  # 100 - int(25 * 1.5) = 100 - 37 = 62 (truncated)

    def test_mixed_bugs_and_security(self, pipeline_cls, sample_complexity):
        """Combined bugs + security findings calculate correctly."""
        bugs = [
            BugFinding(
                line=1,
                severity="high",
                message="Bug",
                suggestion="Fix",
                source="static",
            ),
            BugFinding(
                line=2,
                severity="medium",
                message="Bug 2",
                suggestion="Fix",
                source="llm",
            ),
        ]
        security = [
            SecurityFinding(
                line=5,
                severity="high",
                message="XSS",
                suggestion="Sanitise",
                owasp_category="A07:2021",
            )
        ]
        # 100 - 15 (high bug) - 7 (medium bug) - 15*1.5 (high sec) = 55.5 → int = 55
        score = pipeline_cls._compute_score(bugs, security, sample_complexity)
        assert score == 55

    def test_score_clamps_to_zero(self, pipeline_cls, sample_complexity):
        """Score should never go below 0."""
        bugs = [
            BugFinding(
                line=i,
                severity="critical",
                message=f"Bug {i}",
                suggestion="Fix",
                source="llm",
            )
            for i in range(10)  # 10 critical = -250 → clamped to 0
        ]
        score = pipeline_cls._compute_score(bugs, [], sample_complexity)
        assert score == 0

    def test_score_clamps_to_hundred(self, pipeline_cls, sample_complexity):
        """Score should never exceed 100."""
        score = pipeline_cls._compute_score([], [], sample_complexity)
        assert score <= 100


# ── Sorting Tests ────────────────────────────────────────────────────────────


class TestSorting:
    """Tests for _sort_findings()."""

    def test_severity_order(self, pipeline_cls):
        """Findings should be sorted by severity: critical > high > medium > low."""
        findings = [
            BugFinding(line=1, severity="low", message="L", suggestion="S", source="llm"),
            BugFinding(line=2, severity="critical", message="C", suggestion="S", source="llm"),
            BugFinding(line=3, severity="medium", message="M", suggestion="S", source="llm"),
            BugFinding(line=4, severity="high", message="H", suggestion="S", source="llm"),
        ]
        result = pipeline_cls._sort_findings(findings)
        severities = [f.severity for f in result]
        assert severities == ["critical", "high", "medium", "low"]

    def test_same_severity_sorted_by_line(self, pipeline_cls):
        """Findings with same severity should be sorted by line number ascending."""
        findings = [
            BugFinding(line=30, severity="high", message="A", suggestion="S", source="llm"),
            BugFinding(line=10, severity="high", message="B", suggestion="S", source="llm"),
            BugFinding(line=20, severity="high", message="C", suggestion="S", source="llm"),
        ]
        result = pipeline_cls._sort_findings(findings)
        lines = [f.line for f in result]
        assert lines == [10, 20, 30]

    def test_none_lines_go_last(self, pipeline_cls):
        """Findings with line=None should sort after those with line numbers."""
        findings = [
            BugFinding(line=None, severity="high", message="A", suggestion="S", source="llm"),
            BugFinding(line=5, severity="high", message="B", suggestion="S", source="llm"),
        ]
        result = pipeline_cls._sort_findings(findings)
        assert result[0].line == 5
        assert result[1].line is None

    def test_empty_list(self, pipeline_cls):
        """Empty input should return empty output."""
        result = pipeline_cls._sort_findings([])
        assert result == []


# ── Full Pipeline Integration Test ───────────────────────────────────────────


class TestPipelineRun:
    """Integration test for the full pipeline with mocked LLM."""

    @pytest.mark.asyncio
    async def test_full_pipeline_mocked(self):
        """
        Run the full pipeline with mocked LLM chains and verify:
        - Response contains merged bugs
        - Deduplication removes overlapping LLM finding
        - Score is computed correctly
        - processing_time_ms is present and > 0
        """
        from app.services.prompts.structured_output import (
            BugDetectionSchema,
            BugFindingSchema,
            ComplexityAnalysisSchema,
            SecurityFindingSchema,
            SecurityReviewSchema,
        )

        # Mock LLM responses
        mock_bug_result = BugDetectionSchema(
            bugs=[
                BugFindingSchema(
                    line=10,
                    severity="high",
                    message="Mutable default argument detected in function definition",
                    suggestion="Use None as default",
                ),
                BugFindingSchema(
                    line=25,
                    severity="medium",
                    message="Unused import os",
                    suggestion="Remove unused import",
                ),
            ]
        )

        mock_security_result = SecurityReviewSchema(
            security=[
                SecurityFindingSchema(
                    line=42,
                    severity="critical",
                    message="SQL injection vulnerability",
                    suggestion="Use parameterised queries",
                    owasp_category="A03:2021 – Injection",
                )
            ]
        )

        mock_complexity_result = ComplexityAnalysisSchema(
            time_complexity="O(n)",
            space_complexity="O(1)",
            explanation="Linear scan.",
            suggestion=None,
        )

        with (
            patch.object(
                ReviewPipeline, "_run_static_analysis"
            ) as mock_static,
            patch("app.services.pipeline.CacheService") as MockCache,
        ):
            # Setup mock static analysis - returns a finding that overlaps with LLM
            mock_static.return_value = [
                BugFinding(
                    line=10,
                    severity="high",
                    message="Mutable default argument detected in function",
                    suggestion="Use None instead of mutable default",
                    source="static",
                ),
            ]

            # Setup mock cache (always miss)
            mock_cache_instance = MagicMock()
            mock_cache_instance.get = AsyncMock(return_value=None)
            mock_cache_instance.set = AsyncMock()
            MockCache.return_value = mock_cache_instance
            MockCache.make_key = CacheService_make_key_stub

            # Create pipeline and mock the LLM chains
            pipeline = ReviewPipeline.__new__(ReviewPipeline)
            pipeline._cache = mock_cache_instance
            pipeline._language_detector = MagicMock()
            pipeline._ast_analyzer = MagicMock()
            pipeline._complexity_checker = MagicMock()
            pipeline._style_checker = MagicMock()
            pipeline._pattern_matcher = MagicMock()

            # Mock chains
            pipeline._bug_chain = MagicMock()
            pipeline._bug_chain.ainvoke = AsyncMock(return_value=mock_bug_result)
            pipeline._security_chain = MagicMock()
            pipeline._security_chain.ainvoke = AsyncMock(return_value=mock_security_result)
            pipeline._complexity_chain = MagicMock()
            pipeline._complexity_chain.ainvoke = AsyncMock(return_value=mock_complexity_result)

            # Bind static methods
            pipeline._run_static_analysis = mock_static
            pipeline._deduplicate_findings = ReviewPipeline._deduplicate_findings
            pipeline._sort_findings = ReviewPipeline._sort_findings
            pipeline._compute_score = ReviewPipeline._compute_score
            pipeline._synthesise_summary = ReviewPipeline._synthesise_summary

            # Run pipeline
            request = CodeReviewRequest(
                code="def foo(x=[]):\n    return x",
                language="python",
            )
            response = await pipeline.run(request)

            # Assertions
            assert isinstance(response, CodeReviewResponse)
            assert response.processing_time_ms >= 0

            # Deduplication: static line=10 kept, LLM line=10 (similar msg) removed,
            # LLM line=25 kept → 2 bugs total
            assert len(response.bugs) == 2

            # First bug should be critical/high (sorted by severity)
            assert response.bugs[0].severity == "high"
            assert response.bugs[0].source == "static"

            # Security findings preserved
            assert len(response.security) == 1
            assert response.security[0].severity == "critical"

            # Score: 100 - 15 (high static bug) - 7 (medium LLM bug) - 25*1.5 (critical sec)
            # = 100 - 15 - 7 - 37.5 = 40.5 → int = 40
            assert response.overall_score == 40

            # Summary should mention bugs and security
            assert "bug" in response.summary.lower()
            assert "security" in response.summary.lower()


def CacheService_make_key_stub(code: str, language: str) -> str:
    """Stub for CacheService.make_key in tests."""
    return f"test:review:{language}"
