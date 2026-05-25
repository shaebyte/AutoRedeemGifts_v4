import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.config import GIFT_CODE_API
from ..deps import get_db

router = APIRouter(prefix="/gift-codes", tags=["gift-codes"])


@router.get("")
async def list_codes(db=Depends(get_db)):
    async with db.execute(
        "SELECT code, created_at FROM gift_codes ORDER BY created_at DESC"
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]


@router.get("/live")
async def live_codes():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GIFT_CODE_API, timeout=10.0)
            resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"External API error: {e}")
    return resp.json()
