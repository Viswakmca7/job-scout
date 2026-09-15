from __future__ import annotations

import logging

import httpx

from .config import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL

logger = logging.getLogger("vjobs.email")

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


async def send_magic_link_email(to_email: str, link_url: str) -> bool:
    """Send the sign-in link. Returns True if actually emailed, False if it was only
    logged (SendGrid not configured) — callers should treat both as success to the
    end user, since logging it is the deliberate fallback for local/unconfigured runs."""
    if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
        logger.info("SendGrid not configured — magic link for %s: %s", to_email, link_url)
        return False

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": SENDGRID_FROM_EMAIL, "name": "Vjobs"},
        "subject": "Your Vjobs sign-in link",
        "content": [
            {
                "type": "text/plain",
                "value": f"Sign in to Vjobs: {link_url}\n\nThis link expires in 15 minutes and can only be used once.",
            },
            {
                "type": "text/html",
                "value": (
                    f'<p>Click to sign in to Vjobs:</p><p><a href="{link_url}">{link_url}</a></p>'
                    "<p>This link expires in 15 minutes and can only be used once.</p>"
                ),
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SENDGRID_URL,
            json=payload,
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
            timeout=15.0,
        )
    if resp.status_code >= 300:
        logger.error("SendGrid send failed (%s): %s", resp.status_code, resp.text[:500])
        return False
    return True
