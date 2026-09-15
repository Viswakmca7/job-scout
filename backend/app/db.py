from __future__ import annotations

import logging

import asyncpg

from .config import DATABASE_URL

logger = logging.getLogger("vjobs.db")

_pool: asyncpg.Pool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS magic_links (
    token TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        # Render's internal connection string doesn't need/support SSL; the external
        # one requires it. Try plain first, fall back to requiring SSL.
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        except (ConnectionError, OSError, asyncpg.PostgresError):
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, ssl="require")
    return _pool


async def init_db() -> None:
    if not DATABASE_URL:
        logger.info("DATABASE_URL not set — accounts/sign-in disabled")
        return
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(SCHEMA)
        logger.info("database schema ready")
    except Exception:
        logger.exception("failed to initialize database — accounts/sign-in will be unavailable")
