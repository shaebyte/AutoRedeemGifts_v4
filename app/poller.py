import asyncio
import logging

import httpx

from app import database, redeemer
from app.config import GIFT_CODE_API

logger = logging.getLogger(__name__)

POLL_INTERVAL = 5 * 60


async def _fetch_codes() -> list[str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(GIFT_CODE_API, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    return [item['code'] for item in data.get('data', {}).get('giftCodes', [])]


def _on_redeemer_done(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("Redeemer crashed: %s", task.exception())


async def poll_once() -> None:
    logger.info("Polling %s for new gift codes...", GIFT_CODE_API)
    try:
        codes = await _fetch_codes()
    except Exception as exc:
        logger.error("Failed to fetch gift codes: %s", exc)
        return

    found_new = False
    for code in codes:
        if await database.save_gift_code(code):
            logger.info("New code: %s", code)
            found_new = True
            task = asyncio.create_task(redeemer.redeem_all(code))
            task.add_done_callback(_on_redeemer_done)

    if not found_new:
        logger.info("No new codes found.")


async def run_poller() -> None:
    while True:
        await poll_once()
        logger.info("Next poll in %d minutes.", POLL_INTERVAL // 60)
        await asyncio.sleep(POLL_INTERVAL)
