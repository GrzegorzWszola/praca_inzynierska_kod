import secrets
from typing import Annotated
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

router = APIRouter(prefix="/session", tags=["session"])
COOKIE_NAME = "sid"

@router.post("/init")
def init_session(response: Response, sid: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if not sid or len(sid) < 32:
        sid = secrets.token_urlsafe(32)
        response.set_cookie(
            COOKIE_NAME, sid,
            httponly=True,
            secure=False,        # lokalnie na http:// ustaw False
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )
    return {"ok": True}

def require_sid(sid: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> str:
    if not sid or len(sid) < 32:
        raise HTTPException(401, "No session")
    return sid

CookieDep = Annotated[str, Depends(require_sid)]
