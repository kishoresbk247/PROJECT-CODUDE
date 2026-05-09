"""
CoDude — LLM Service (Day 06 — Retry Logic)

Base service class that wraps LangChain's ChatOpenAI integration.
Provides the foundation for all AI-powered features in CoDude.

Why LangChain over raw OpenAI SDK?
    - LCEL (LangChain Expression Language) lets us compose chains with |
      (prompt | llm | parser) and swap any component without touching the rest.
    - Built-in .with_structured_output() gives us validated Pydantic models
      directly from the LLM — no manual JSON parsing or retry logic.
    - Future-proof: adding caching, fallback models, or streaming is a
      one-line change instead of a rewrite.

Model choice: gpt-4o-mini
    - Best cost/performance ratio for code review tasks.
    - Supports structured output (function calling) natively.
    - Temperature=0 for deterministic, reproducible reviews.

Day 06 additions:
    - tenacity @retry decorator on invoke() and ainvoke() calls
    - Retries up to 3 times on RateLimitError or APIConnectionError
    - Exponential backoff starting at 2 seconds (2s → 4s → 8s)
    - Logs each retry attempt for observability
"""

import logging

import openai
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Thin wrapper around LangChain's ChatOpenAI with retry logic.

    Usage:
        llm_service = LLMService()
        response = await llm_service.invoke("Explain Python decorators")
        structured = await llm_service.invoke_structured(prompt, MyModel)
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0) -> None:
        """
        Initialise the LLM with the given model and temperature.

        Args:
            model:       OpenAI model name (default: gpt-4o-mini).
            temperature: Sampling temperature (0 = deterministic).
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY,
        )

    @retry(
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APIConnectionError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def invoke(self, prompt: str) -> str:
        """
        Send a plain-text prompt to the LLM and return the text response.

        Retries up to 3 times on OpenAI rate-limit or connection errors
        with exponential backoff (2s → 4s → 8s).

        Args:
            prompt: The user prompt string.

        Returns:
            The model's text response as a string.
        """
        response = await self.llm.ainvoke(prompt)
        return response.content

    def with_structured_output(self, schema: type[BaseModel]) -> ChatOpenAI:
        """
        Return a runnable that forces the LLM to respond with a
        structured output matching the given Pydantic schema.

        This uses OpenAI's function-calling under the hood, so the
        response is guaranteed to parse into the schema.

        Args:
            schema: A Pydantic BaseModel subclass defining the output shape.

        Returns:
            A LangChain Runnable that outputs an instance of `schema`.
        """
        return self.llm.with_structured_output(schema)
