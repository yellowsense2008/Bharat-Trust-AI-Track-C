"""
session_manager.py
In-memory session store with auto-expiry (10 minutes).
Provides create / get / update operations for complaint intake sessions.
"""

import time
from typing import Optional

# ─── Constants ────────────────────────────────────────────────────────────────

SESSION_TTL_SECONDS = 600  # 10 minutes


# ─── Session store ────────────────────────────────────────────────────────────

_sessions: dict = {}


def _fresh_session() -> dict:
    return {
        "step": 1,
        "data": {
            "category": None,
            "subcategory": None,
            "amount": None,
            "time": None,
            "issue": None,
        },
        "completed": False,
        "last_updated": time.time(),
    }


def _is_expired(session: dict) -> bool:
    return (time.time() - session["last_updated"]) > SESSION_TTL_SECONDS


def _touch(session: dict) -> None:
    session["last_updated"] = time.time()


# ─── Public API ───────────────────────────────────────────────────────────────

def get_or_create(session_id: str) -> dict:
    """Return existing (non-expired) session or create a fresh one."""
    if session_id in _sessions and not _is_expired(_sessions[session_id]):
        return _sessions[session_id]
    # Expired or new → start fresh
    _sessions[session_id] = _fresh_session()
    return _sessions[session_id]


def update(session_id: str, session: dict) -> None:
    """Persist session changes and refresh the TTL clock."""
    _touch(session)
    _sessions[session_id] = session


def reset(session_id: str) -> None:
    """Force-reset a session (useful for testing or explicit resets)."""
    _sessions[session_id] = _fresh_session()


def get_snapshot(session_id: str) -> Optional[dict]:
    """Return a copy of the session data without mutating state."""
    sess = _sessions.get(session_id)
    if sess and not _is_expired(sess):
        return dict(sess)
    return None
