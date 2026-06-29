"""Minimal FastAPI host for the parse endpoint.

This is a deliberately small application that exists so the server-side parser
introduced by the SheetJS migration is actually runnable today. The legacy
``backend/main.py`` and ``backend/main_enhanced.py`` are off-limits to new code
(see their STATUS headers), and the full web backend is Epic 3 (Phase 3). When
that arrives it will own application assembly; this module folds into it.

Run locally::

    uvicorn backend.api.app:app --port 8000

The Vite dev server proxies ``/api`` here (see ``vite.config.ts``), so the
browser talks to it same-origin and no CORS configuration is required in dev.
"""

from __future__ import annotations

from fastapi import FastAPI

from backend.api.parse_file import router as parse_router

app = FastAPI(title="SavvyCortex API", version="0.1.0")
app.include_router(parse_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for local dev and the Vite proxy."""
    return {"status": "ok"}
