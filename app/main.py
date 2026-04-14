"""
main.py — FastAPI application entry-point for Track C Grievance System.

Cloud Run startup contract
--------------------------
Cloud Run sends a health-check to GET / or GET /health immediately after
the container starts.  The server MUST bind to $PORT and respond within
the deployment timeout (~4 min, but target <10 s).

Rules followed here:
* No heavy ML imports at module level.
* DB table creation is fast (DDL only, no model inference).
* All ML models load lazily on first endpoint call.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Routers (no heavy ML code in any of these at import time) ─────────────
from app.api.auth_routes import router as auth_router
from app.api.complaint_routes import router as complaint_router
from app.api.citizen_routes import router as citizen_router
from app.api.department_routes import router as department_router
from app.api.analytics_routes import router as analytics_router
from app.api.lifecycle_routes import router as lifecycle_router
from app.api.voice_routes import router as voice_router
from app.api.chat_routes import router as chat_router
from app.api.admin_routes import router as admin_router
from app.api.status_routes import router as status_router
from app.api.conversation_routes import router as conversation_router
from app.services.resolution_ai_service import preload

# ── DB (fast — engine creation, no I/O until first query) ────────────────
from app.core.database import engine, Base

# Import model classes so SQLAlchemy registers them with Base.metadata
from app.models import user, complaint  # noqa: F401
from app.models import conversation_session  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes AFTER uvicorn has bound the socket and BEFORE the first request.
    Keep this fast — only DB DDL and env-var validation here.
    ML models load lazily on first speech endpoint call.
    """
    # 1. Warn about missing secrets (don't crash — let health check pass first)
    _required = ["SECRET_KEY", "GROQ_API_KEY", "DATABASE_URL"]
    _missing = [k for k in _required if not os.getenv(k)]
    if _missing:
        logger.warning(
            "⚠️  Missing env vars: %s — configure them in Cloud Run secrets.",
            ", ".join(_missing),
        )

    # 2. Create DB tables (fast DDL, no model download)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified / created.")
    except Exception as exc:
        logger.error("❌ DB init failed: %s", exc)
        # Don't re-raise — allow container to start; DB errors surface per-request

    # 3. Preload AI models
    preload()

    logger.info(
        "🚀 Server ready — listening on port %s",
        os.getenv("PORT", "8080"),
    )
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("🛑 Server shutting down.")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Track C Grievance System",
    version="1.0.0",
    description="AI-powered citizen grievance management system.",
    lifespan=lifespan,
)
# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "https://rbi-track-c-api-2333988202.asia-south1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(complaint_router)
app.include_router(citizen_router)
app.include_router(department_router)
app.include_router(analytics_router)
app.include_router(lifecycle_router)
app.include_router(voice_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(status_router)
app.include_router(conversation_router)


# ── Root & health endpoints ───────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Service root — returned immediately, no DB or ML calls."""
    return {
        "service": "Track C Grievance System API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    """
    Cloud Run liveness / readiness probe.
    Must respond in < 1 s — no DB or ML calls here.
    """
    return {"status": "ok"}