"""
Pytest configuration for CoDude backend tests.

Sets anyio backend to asyncio (used by pytest-asyncio / anyio fixtures).
"""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend for all tests."""
    return "asyncio"
