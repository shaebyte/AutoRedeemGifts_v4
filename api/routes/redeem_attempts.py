from fastapi import APIRouter, Depends, Query
from ..deps import get_db
from ..auth import require_mod

router = APIRouter(
    prefix="/redeem-attempts",
    tags=["redeem"],
    dependencies=[Depends(require_mod)],
)


@router.get("")
async def list_attempts(
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: str | None = Query(None),
    status: str = Query("all"),
):
    offset = (page - 1) * limit

    conditions = []
    params = []

    if search:
        conditions.append("(player_id LIKE ? OR gift_code LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]

    if status in ("success", "failed"):
        conditions.append("status = ?")
        params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with db.execute(
        f"SELECT COUNT(*) FROM redeem_attempts {where}", params
    ) as cur:
        total = (await cur.fetchone())[0]

    async with db.execute(
        f"""
        SELECT player_id, gift_code, status, attempt_count, error_message,
               DATE(redeemed_at) AS redeemed_at
        FROM redeem_attempts
        {where}
        ORDER BY redeemed_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    ) as cur:
        cur.row_factory = lambda c, r: dict(zip([d[0] for d in c.description], r))
        items = await cur.fetchall()

    return {"items": items, "total": total}