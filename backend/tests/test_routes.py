"""
CoDude — Route Tests (Day 02)

Tests the health, version, and review stub endpoints using
pytest + httpx async client against the FastAPI test client.

Run:
    pytest backend/tests/ -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def client():
    """Create an async httpx client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health & Version Tests ───────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health_endpoint(client):
    """GET /health should return 200 with status=ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "codude"


@pytest.mark.anyio
async def test_version_endpoint(client):
    """GET /api/v1/version should return 200 with version info."""
    response = await client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["api_version"] == "v1"
    assert data["service"] == "codude"


# ── Review Stub Tests ────────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "code": "def add(a, b):\n    return a + b",
    "language": "python",
    "filename": "utils.py",
}


@pytest.mark.anyio
async def test_review_full(client):
    """POST /api/v1/review should return 200 with a complete review response."""
    response = await client.post("/api/v1/review", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "bugs" in data
    assert "security" in data
    assert "complexity" in data
    assert "summary" in data
    assert "overall_score" in data

    # Verify types
    assert isinstance(data["bugs"], list)
    assert isinstance(data["security"], list)
    assert isinstance(data["overall_score"], int)
    assert 0 <= data["overall_score"] <= 100


@pytest.mark.anyio
async def test_review_bugs(client):
    """POST /api/v1/review/bugs should return a list of bug findings."""
    response = await client.post("/api/v1/review/bugs", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    # Each bug should have the expected fields
    for bug in data:
        assert "severity" in bug
        assert "message" in bug
        assert "suggestion" in bug
        assert bug["severity"] in ("critical", "high", "medium", "low")


@pytest.mark.anyio
async def test_review_security(client):
    """POST /api/v1/review/security should return a list of security findings."""
    response = await client.post("/api/v1/review/security", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    for finding in data:
        assert "severity" in finding
        assert "message" in finding
        assert "suggestion" in finding
        assert "owasp_category" in finding


@pytest.mark.anyio
async def test_review_complexity(client):
    """POST /api/v1/review/complexity should return complexity analysis."""
    response = await client.post("/api/v1/review/complexity", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert "time_complexity" in data
    assert "space_complexity" in data
    assert "explanation" in data


@pytest.mark.anyio
async def test_review_validation_error(client):
    """POST /api/v1/review with empty body should return 422."""
    response = await client.post("/api/v1/review", json={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_review_empty_code_rejected(client):
    """POST /api/v1/review with empty code string should return 422."""
    response = await client.post(
        "/api/v1/review",
        json={"code": "", "language": "python"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_nonexistent_route(client):
    """GET to a non-existent route should return 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
