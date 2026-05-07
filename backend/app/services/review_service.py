"""
CoDude — Review Service

Orchestrates the AI code review pipeline by composing an LCEL chain:

    prompt | llm.with_structured_output(CodeReviewSchema)

This is the business-logic layer that sits between the router (HTTP
concern) and the LLM (AI concern). The router never touches LangChain
directly — it delegates to ReviewService and gets back a clean
CodeReviewResponse.

Chain architecture (LCEL):
    1. CODE_REVIEW_PROMPT fills in {language} and {code}
    2. The prompt is piped to ChatOpenAI with structured output
    3. The LLM returns a CodeReviewSchema (Pydantic model)
    4. We map that schema to the API's CodeReviewResponse model
"""

from app.models.review import (
    BugFinding,
    CodeReviewRequest,
    CodeReviewResponse,
    ComplexityResult,
    SecurityFinding,
)
from app.services.llm_service import LLMService
from app.services.prompts.base_review import CODE_REVIEW_PROMPT
from app.services.prompts.structured_output import CodeReviewSchema


class ReviewService:
    """
    High-level service for AI-powered code reviews.

    Usage:
        service = ReviewService()
        response = await service.review(request)
    """

    def __init__(self) -> None:
        """Initialise the LLM service and build the LCEL chain."""
        self._llm_service = LLMService()

        # LCEL chain: prompt | llm_with_structured_output
        # The | operator composes these into a single Runnable.
        # Nothing executes until .ainvoke() is called (lazy evaluation).
        self._chain = (
            CODE_REVIEW_PROMPT
            | self._llm_service.with_structured_output(CodeReviewSchema)
        )

    async def review(self, request: CodeReviewRequest) -> CodeReviewResponse:
        """
        Run a full AI code review on the submitted code.

        Args:
            request: The client's code review request containing
                     code, language, and optional filename.

        Returns:
            A CodeReviewResponse with bugs, security findings,
            complexity analysis, summary, and overall score.
        """
        # Invoke the chain with the template variables
        result: CodeReviewSchema = await self._chain.ainvoke({
            "language": request.language,
            "code": request.code,
        })

        # Map the LLM's structured output to our API response models
        return self._to_response(result)

    @staticmethod
    def _to_response(schema: CodeReviewSchema) -> CodeReviewResponse:
        """
        Convert the LLM's CodeReviewSchema into the API's CodeReviewResponse.

        These are intentionally separate models: the schema is owned by
        the AI layer (optimised for LLM function-calling), while the
        response model is owned by the API layer (optimised for clients).
        """
        bugs = [
            BugFinding(
                line=b.line,
                severity=b.severity,
                message=b.message,
                suggestion=b.suggestion,
            )
            for b in schema.bugs
        ]

        security = [
            SecurityFinding(
                line=s.line,
                severity=s.severity,
                message=s.message,
                suggestion=s.suggestion,
                owasp_category=s.owasp_category,
            )
            for s in schema.security
        ]

        complexity = None
        if schema.complexity:
            complexity = ComplexityResult(
                time_complexity=schema.complexity.time_complexity,
                space_complexity=schema.complexity.space_complexity,
                explanation=schema.complexity.explanation,
                brute_force_alternative=schema.complexity.brute_force_alternative,
            )

        return CodeReviewResponse(
            bugs=bugs,
            security=security,
            complexity=complexity,
            summary=schema.summary,
            overall_score=schema.overall_score,
        )
