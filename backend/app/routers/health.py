"""
CoDude — Health & Version Router

Provides operational endpoints for monitoring and diagnostics.

Routes:
    GET /health          — Liveness check (returns {"status": "ok"})
    GET /api/v1/version  — Returns the current API version and build info
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Liveness probe — returns 200 if the service is running.",
)
async def health_check() -> dict:
    """
    Health check endpoint.

    Used by load balancers, container orchestrators (e.g. Kubernetes),
    and uptime monitors to verify the service is alive.
    """
    return {"status": "ok", "service": "codude"}


@router.get(
    "/api/v1/version",
    summary="API version",
    description="Returns the current API version, build, and environment.",
)
async def version() -> dict:
    """
    Version endpoint.

    Returns the current API version string so clients can detect
    compatibility and display build info in their UI.
    """
    return {
        "version": "0.2.0",
        "api_version": "v1",
        "service": "codude",
        "description": "CoDude AI Code Review API",
    }
