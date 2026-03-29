import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base

# Import models so SQLAlchemy creates tables
from app.models import user, complaint

# Import routers
from app.api.auth_routes import router as auth_router
from app.api.complaint_routes import router as complaint_router
from app.api.department_routes import router as department_router
from app.api.analytics_routes import router as analytics_router
from app.api.lifecycle_routes import router as lifecycle_router
from app.api.voice_routes import router as voice_router
from app.api.chat_routes import router as chat_router

logger = logging.getLogger(__name__)


# ── Startup / Shutdown lifecycle ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs AFTER the server has bound to $PORT and is ready to accept requests.
    Heavy initialisation (e.g. ML models) happens here, never at import time.
    """
    # Validate required env vars – warn loudly but don't crash.
    # Crashing here would prevent the container from ever responding to the
    # Cloud Run health check, causing the deployment to fail.
    _required = ["SECRET_KEY", "GROQ_API_KEY", "DATABASE_URL"]
    _missing = [k for k in _required if not os.getenv(k)]
    if _missing:
        logger.warning(
            "⚠️  Missing env vars: %s  — set them in Cloud Run secrets.",
            ", ".join(_missing),
        )

    # Create DB tables (fast – no model download here)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified / created.")
    except Exception as exc:
        logger.error("❌ DB init failed: %s", exc)

    logger.info("🚀 App startup complete – listening on port %s", os.getenv("PORT", "8080"))
    yield
    # ── shutdown ──
    logger.info("🛑 App shutting down.")


# ── Application ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Track C Grievance System",
    version="1.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(complaint_router)
app.include_router(department_router)
app.include_router(analytics_router)
app.include_router(lifecycle_router)
app.include_router(voice_router)
app.include_router(chat_router)


# ── Root & health checks ─────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Track C Grievance System API",
        "status": "running",
    }


@app.get("/health")
def health():
    """Cloud Run uses this path for liveness probes."""
    return {"status": "ok"}