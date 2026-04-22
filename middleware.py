import time
from collections import defaultdict
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

BOT_UA_KEYWORDS = [
    "bot", "crawler", "spider", "scraper", "curl", "wget",
    "python-requests", "go-http-client", "java/", "libwww",
]


class BotBlockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ua = request.headers.get("user-agent", "").lower()
        if any(kw in ua for kw in BOT_UA_KEYWORDS):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        return await call_next(request)


# In-memory store: (ip, tool_id) -> last click timestamp
_click_store: dict[tuple[str, str], float] = defaultdict(float)
CLICK_COOLDOWN = 3600  # 1 hour


def is_duplicate_click(ip: str, tool_id: str) -> bool:
    key = (ip, tool_id)
    now = time.time()
    if now - _click_store[key] < CLICK_COOLDOWN:
        return True
    _click_store[key] = now
    return False
