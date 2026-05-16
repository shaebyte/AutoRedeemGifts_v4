from fastapi import APIRouter, Depends
from ..deps import get_db

router = APIRouter(prefix="/gift-codes", tags=["gift-codes"])


@router.get("")
async def list_codes(db=Depends(get_db)):
    async with db.execute(
        "SELECT code, created_at FROM gift_codes ORDER BY created_at DESC"
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]
