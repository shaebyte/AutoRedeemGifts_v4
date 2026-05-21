import aiosqlite
from app.config import DB_PATH


async def save_gift_code(code: str) -> bool:
    """Saves a new gift code. Returns True if new, False if duplicate."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO gift_codes (code) VALUES (?)", (code,))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_accounts_to_redeem(code: str) -> list[dict]:
    """Returns all non-blacklisted accounts that haven't successfully redeemed this code."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT a.player_id, a.name
            FROM accounts a
            WHERE a.blacklisted = 0
              AND NOT EXISTS (
                  SELECT 1 FROM redeem_attempts ra
                  WHERE ra.player_id = a.player_id
                    AND ra.gift_code = ?
                    AND ra.status = 'success'
              )
            """,
            (code,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def save_attempt(
    code: str,
    player_id: str,
    status: str,
    attempt_count: int = 1,
    error_message: str | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO redeem_attempts (gift_code, player_id, status, attempt_count, error_message)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(gift_code, player_id) DO UPDATE SET
                status        = excluded.status,
                attempt_count = excluded.attempt_count,
                error_message = excluded.error_message,
                redeemed_at   = CURRENT_TIMESTAMP
            """,
            (code, player_id, status, attempt_count, error_message),
        )
        await db.commit()

async def cleanup_old_attempts(days: int = 3) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM redeem_attempts
            WHERE redeemed_at < datetime('now', ?)
        """, (f'-{days} days',))
        await db.commit()        
