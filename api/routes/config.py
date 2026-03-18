from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
import httpx
import asyncio
import re
from datetime import datetime, timedelta

from core.database import db
from core.config import settings

router = APIRouter()

BROWSER_KEYWORDS = ["Mozilla", "Chrome", "Safari", "Firefox", "Edge", "Opera", "Trident"]

# Config cache
_config_cache = {
    "content": None,
    "updated_at": None,
}
CACHE_TTL = timedelta(minutes=5)

BROWSER_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhiteLis VPN</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 40px;
            max-width: 500px;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .icon { font-size: 4em; margin-bottom: 20px; }
        p { color: #a0a0a0; line-height: 1.6; }
        .instruction {
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            margin-top: 30px;
            text-align: left;
        }
        .instruction li { margin: 10px 0; color: #e0e0e0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔐</div>
        <h1>WhiteLis VPN</h1>
        <p>Эта ссылка предназначена для VPN-клиента, а не для браузера.</p>
        <div class="instruction">
            <strong>Как использовать:</strong>
            <p>Вставьте ссылку в v2Box (Android/iOS) как подписку.</p>
        </div>
    </div>
</body>
</html>
"""


def is_browser(user_agent: str) -> bool:
    """Check if request is from a browser."""
    if not user_agent:
        return False
    return any(keyword in user_agent for keyword in BROWSER_KEYWORDS)


async def get_cached_config() -> str:
    """Get config with caching. Updates every 5 minutes."""
    now = datetime.now()

    # Check if cache is valid
    if (_config_cache["content"] is not None and
        _config_cache["updated_at"] is not None and
        now - _config_cache["updated_at"] < CACHE_TTL):
        return _config_cache["content"]

    # Fetch fresh config
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.config_url, timeout=60.0)
        response.raise_for_status()
        _config_cache["content"] = response.text
        _config_cache["updated_at"] = now

    return _config_cache["content"]


@router.get("/config/{token}")
async def get_config(token: str, request: Request):
    """
    Get VPN config by user token.
    Returns config only if user has active subscription.
    Shows instruction page for browsers.
    """
    user_agent = request.headers.get("user-agent", "")

    # If browser, show instruction page
    if is_browser(user_agent):
        return HTMLResponse(content=BROWSER_HTML)

    # Check if user exists and has active subscription
    user = await db.get_user_by_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid token")

    has_subscription = await db.has_active_subscription(user.id)

    if not has_subscription:
        raise HTTPException(
            status_code=403,
            detail="Subscription expired. Please renew your subscription."
        )

    # Get config (cached)
    try:
        config_content = await get_cached_config()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch config: {str(e)}"
        )

    # Replace profile-title with our branding
    config_content = re.sub(
        r'^# profile-title:.*$',
        '# profile-title: WhiteLis VPN',
        config_content,
        count=1,
        flags=re.MULTILINE
    )

    return PlainTextResponse(
        content=config_content,
        media_type="text/plain"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
