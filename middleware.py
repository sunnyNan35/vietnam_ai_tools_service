import time
from collections import defaultdict
from functools import wraps
from fastapi import HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

# Admin token store: token -> (expires_at, created_at)
_token_store: dict[str, float] = {}

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


def verify_admin_token(token: str) -> bool:
    if token not in _token_store:
        return False
    expires_at = _token_store[token]
    if time.time() > expires_at:
        del _token_store[token]
        return False
    return True


def add_admin_token(token: str, expires_at: float):
    _token_store[token] = expires_at


def require_admin_auth(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
        token = auth_header[7:]
        if not verify_admin_token(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")
        return await func(request, *args, **kwargs)
    return wrapper
