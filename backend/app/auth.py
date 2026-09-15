from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from .config import MAGIC_LINK_TTL_MINUTES, SESSION_TTL_DAYS
from .db import get_pool


async def create_magic_link(email: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO magic_links (token, email, expires_at) VALUES ($1, $2, $3)",
            token,
            email.lower().strip(),
            expires_at,
        )
    return token


async def verify_magic_link(token: str) -> str | None:
    """Consumes the token if valid. Returns a new session token, or None if the
    magic link was invalid, expired, or already used."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT email, expires_at, used_at FROM magic_links WHERE token = $1 FOR UPDATE",
                token,
            )
            if row is None or row["used_at"] is not None or row["expires_at"] < datetime.now(timezone.utc):
                return None

            await conn.execute("UPDATE magic_links SET used_at = now() WHERE token = $1", token)

            user_id = await conn.fetchval(
                """
                INSERT INTO users (email) VALUES ($1)
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
                """,
                row["email"],
            )

            session_token = secrets.token_urlsafe(32)
            session_expires = datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)
            await conn.execute(
                "INSERT INTO sessions (token, user_id, expires_at) VALUES ($1, $2, $3)",
                session_token,
                user_id,
                session_expires,
            )
    return session_token


async def get_user_email_from_session(session_token: str | None) -> str | None:
    if not session_token:
        return None
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT u.email FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = $1 AND s.expires_at > now()
            """,
            session_token,
        )


async def delete_session(session_token: str | None) -> None:
    if not session_token:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM sessions WHERE token = $1", session_token)
