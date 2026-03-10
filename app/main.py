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


app = FastAPI(
    title="Track C Grievance System",
    version="1.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


# CORS configuration (for frontend access)
origins = [
    "http://localhost:3000",
    "https://*.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth_router)
app.include_router(complaint_router)
app.include_router(department_router)
app.include_router(analytics_router)
app.include_router(lifecycle_router)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Track C Grievance System API",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}