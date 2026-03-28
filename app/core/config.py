import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_expire_raw = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

_REQUIRED = {
    "DATABASE_URL": DATABASE_URL,
    "SECRET_KEY": SECRET_KEY,
    "ALGORITHM": ALGORITHM,
    "ACCESS_TOKEN_EXPIRE_MINUTES": _expire_raw,
    "GROQ_API_KEY": GROQ_API_KEY,
}

_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing)}. "
        "Set them in .env or Cloud Run secrets before starting."
    )

ACCESS_TOKEN_EXPIRE_MINUTES = int(_expire_raw)