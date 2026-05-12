import asyncio
import logging

import httpx

from app import database, redeemer
from app.config import GIFT_CODE_API, REDEEM_API

logger = logging.getLogger(__name__)

POLL_INTERVAL = 15 * 60  # seconds
MAX_ATTEMPTS = 2

_sem = asyncio.Semaphore(1)


async def _redeem_account(client: httpx.AsyncClient, code: str, player_id: str, naam: str) -> None:
    async with _sem:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = await redeemer.redeem_code(client, player_id, code, REDEEM_API)

                if redeemer.is_success(resp) or redeemer.is_already_redeemed(resp):
                    await database.save_attempt(code, player_id, 'success', attempt)
                    logger.info("[%s] %s (%s) — success on attempt %d", code, naam, player_id, attempt)
                    return

                msg = resp.get('msg', '')
                if attempt < MAX_ATTEMPTS and not redeemer.is_permanent_failure(resp):
                    logger.warning(
                        "[%s] %s (%s) — attempt %d failed (%s), retrying...",
                        code, naam, player_id, attempt, msg,
                    )
                    await asyncio.sleep(5)
                else:
                    await database.save_attempt(code, player_id, 'failed', attempt, msg)
                    logger.error(
                        "[%s] %s (%s) — failed after %d attempts: %s",
                        code, naam, player_id, attempt, msg,
                    )
                    return

            except Exception as exc:
                if attempt < MAX_ATTEMPTS:
                    logger.warning(
                        "[%s] %s (%s) — attempt %d error (%s), retrying...",
                        code, naam, player_id, attempt, exc,
                    )
                    await asyncio.sleep(5)
                else:
                    await database.save_attempt(code, player_id, 'error', attempt, str(exc))
                    logger.error(
                        "[%s] %s (%s) — error after %d attempts: %s",
                        code, naam, player_id, attempt, exc,
                    )


async def _fetch_codes() -> list[str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(GIFT_CODE_API, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    return [item['code'] for item in data.get('data', {}).get('giftCodes', [])]


async def poll_once() -> None:
    logger.info("Polling %s for new gift codes...", GIFT_CODE_API)
    try:
        codes = await _fetch_codes()
    except Exception as exc:
        logger.error("Failed to fetch gift codes: %s", exc)
        return

    new_codes: list[str] = []
    for code in codes:
        if await database.save_gift_code(code):
            logger.info("New code: %s", code)
            new_codes.append(code)

    if not new_codes:
        logger.info("No new codes found.")
        return

    async with httpx.AsyncClient() as client:
        for code in new_codes:
            accounts = await database.get_accounts_to_redeem(code)
            if not accounts:
                logger.info("[%s] No accounts to redeem for.", code)
                continue
            logger.info("[%s] Redeeming for %d account(s)...", code, len(accounts))
            await asyncio.gather(
                *[_redeem_account(client, code, acc['player_id'], acc['name']) for acc in accounts]
            )


async def run_poller() -> None:
    while True:
        await poll_once()
        logger.info("Next poll in %d minutes.", POLL_INTERVAL // 60)
        await asyncio.sleep(POLL_INTERVAL)
