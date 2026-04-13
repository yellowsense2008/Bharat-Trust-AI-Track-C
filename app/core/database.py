import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Detect environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# ---------------- DATABASE CONFIG ----------------

if ENVIRONMENT == "production":
    # Use PostgreSQL in production
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # Use SQLite locally for development
    DATABASE_URL = "sqlite:///./test.db"

# ---------------- SQLALCHEMY ENGINE ----------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# ---------------- SESSION ----------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# ---------------- DB DEPENDENCY ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()