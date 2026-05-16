from fastapi import APIRouter, Depends
from ..deps import get_db
from ..auth import require_mod

router = APIRouter(
    prefix="/redeem-attempts",
    tags=["redeem"],
    dependencies=[Depends(require_mod)],
)


@router.get("")
async def list_attempts(db=Depends(get_db)):
    async with db.execute(
        """
        SELECT player_id, gift_code, status, attempt_count, error_message, redeemed_at
        FROM redeem_attempts
        ORDER BY redeemed_at DESC
        LIMIT 200
        """
    ) as cur:
        return [dict(r) for r in await cur.fetchall()]
