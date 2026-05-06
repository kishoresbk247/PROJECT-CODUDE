"""
CoDude — Main FastAPI Application

Central application factory that wires together:
    - CORS middleware (allows frontend at localhost:3000)
    - Global exception handlers (HTTPException + unhandled errors)
    - Health / version router  (GET /health, GET /api/v1/version)
    - Review router            (POST /api/v1/review/*)

All business logic lives in routers and services — this file is
purely configuration and middleware.
"""

import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import health, review

# ── Application Instance ─────────────────────────────────────────────────────

app = FastAPI(
    title="CoDude API",
    description="AI-powered code review assistant backend",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ──────────────────────────────────────────────────────────
# Allow the React/Next.js frontend running on localhost:3000 to call the API.
# In production this should be restricted to the actual frontend domain.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handlers ───────────────────────────────────────────────
# These catch exceptions that escape route handlers and return a uniform
# JSON error envelope so the frontend never receives raw HTML stack traces.


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPExceptions and return a structured JSON response.

    This ensures that all HTTP errors (404, 422, etc.) are returned in
    a consistent format: {"error": ..., "detail": ..., "status_code": ...}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    Logs the full traceback server-side but returns a generic 500 to
    the client to avoid leaking internal implementation details.
    """
    # Log the full traceback for debugging (visible in uvicorn output)
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "detail": "Internal server error. Please try again later.",
            "status_code": 500,
        },
    )


# ── Register Routers ────────────────────────────────────────────────────────
# Each router owns a set of related endpoints. Registering them here makes
# them available at their defined prefixes.

app.include_router(health.router)
app.include_router(review.router)
