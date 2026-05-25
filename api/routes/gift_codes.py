import time
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.config import GIFT_CODE_API
from ..deps import get_db

router = APIRouter(prefix="/gift-codes", tags=["gift-codes"])

_CACHE_TTL = 15 * 60  # 15 minutes
_cache: dict = {"data": None, "expires_at": 0.0}


@router.get("")
async def list_codes(db=Depends(get_db)):
    async with db.execute(
        "SELECT code, created_at FROM gift_codes ORDER BY created_at DESC"
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]


@router.get("/live")
async def live_codes():
    now = time.monotonic()
    if _cache["data"] is not None and now < _cache["expires_at"]:
        return JSONResponse(
            content=_cache["data"],
            headers={"Cache-Control": f"public, max-age={_CACHE_TTL}"},
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GIFT_CODE_API, timeout=10.0)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")

    data = resp.json()
    _cache["data"] = data
    _cache["expires_at"] = now + _CACHE_TTL

    return JSONResponse(
        content=data,
        headers={"Cache-Control": f"public, max-age={_CACHE_TTL}"},
    )
