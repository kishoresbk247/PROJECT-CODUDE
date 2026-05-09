"""
CoDude — Rate Limiter Middleware (Day 06)

Uses slowapi (a Starlette/FastAPI wrapper around the 'limits' library)
to enforce per-IP rate limits on the review endpoint.

Why rate limit?
    - OpenAI API calls cost money — a single abusive client could rack
      up hundreds of dollars in minutes.
    - LLM calls are slow (2–8s) — too many concurrent requests degrade
      service for everyone.
    - 10 requests/minute per IP is generous for a code review tool
      (no human reviews code that fast) but blocks automated abuse.

How it works:
    - slowapi tracks request counts per IP using an in-memory store.
    - When the limit is exceeded, it returns HTTP 429 Too Many Requests
      with a Retry-After header telling the client when to try again.
    - The key function extracts the client IP from the request.

Production note:
    In production behind a load balancer, use X-Forwarded-For header
    parsing instead of request.client.host (the default key function
    handles this via slowapi's get_remote_address).
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ── Limiter Instance ─────────────────────────────────────────────────────────
# key_func: extracts the client IP to use as the rate-limit key.
# default_limits: global fallback (applied to routes without explicit limits).
# We set explicit limits on the review route, so this is just a safety net.

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
)


def setup_rate_limiter(app):
    """
    Attach the rate limiter to a FastAPI application.

    This must be called during app startup (in main.py) to:
    1. Store the limiter in app.state so slowapi can access it.
    2. Register the 429 exception handler for RateLimitExceeded errors.

    Args:
        app: The FastAPI application instance.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
