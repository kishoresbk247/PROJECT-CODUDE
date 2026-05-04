"""
CoDude — Main FastAPI Application
Minimal server with a health check endpoint.
"""

from fastapi import FastAPI

app = FastAPI(
    title="CoDude API",
    description="AI-powered coding assistant backend",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "ok", "service": "codude"}
