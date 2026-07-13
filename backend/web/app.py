"""
FastAPI micro web server — keeps Render's HTTP health check satisfied
and exposes read-only API endpoints for the dashboard UI.
"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.db.client import get_db

logger = logging.getLogger(__name__)

app = FastAPI(title="LifeOS", docs_url=None, redoc_url=None)

_DIST = Path(__file__).parent.parent / "dist"


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/saves")
async def list_saves(limit: int = 50, offset: int = 0):
    try:
        db = get_db()
        result = (
            db.table("saved_items")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        count_res = db.table("saved_items").select("id", count="exact").execute()
        return {"items": result.data, "total": count_res.count or 0}
    except Exception as exc:
        logger.error("api/saves error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/saves/{save_code}")
async def get_save(save_code: str):
    try:
        db = get_db()
        result = db.table("saved_items").select("*").eq("save_code", save_code.upper()).maybeSingle().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Not found")
        return result.data
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("api/saves/%s error: %s", save_code, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/bio")
async def get_bio():
    try:
        db = get_db()
        result = db.table("bio_state").select("*").limit(1).execute()
        return result.data[0] if result.data else {}
    except Exception as exc:
        logger.error("api/bio error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    try:
        db = get_db()
        result = (
            db.table("bot_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"logs": result.data}
    except Exception as exc:
        logger.error("api/logs error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Static files (React build) ────────────────────────────────────────────────

def mount_static():
    if _DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            index = _DIST / "index.html"
            if index.exists():
                return FileResponse(str(index))
            return JSONResponse({"status": "LifeOS API running"})
    else:
        @app.get("/")
        async def root():
            return {"status": "LifeOS API running — no UI build found"}


mount_static()
