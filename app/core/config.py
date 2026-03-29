import os
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_expire_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

# Warn at import time but do NOT raise – Cloud Run injects env vars after
# the process starts; crashing here prevents the container from ever binding
# to $PORT (triggering the "container failed to start" error).
_REQUIRED = {
    "DATABASE_URL": DATABASE_URL,
    "SECRET_KEY": os.getenv("SECRET_KEY"),
    "GROQ_API_KEY": GROQ_API_KEY,
}
_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    logger.warning(
        "⚠️  Missing environment variables: %s – "
        "ensure they are set in Cloud Run secrets/env before requests arrive.",
        ", ".join(_missing),
    )

ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_raw)