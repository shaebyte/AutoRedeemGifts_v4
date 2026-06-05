import asyncio
import hashlib
import logging
import time

import httpx

from app import database
from app.config import REDEEM_API, REDEEM_SECRET

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 5
RATE_LIMIT_BACKOFF = 60
INTER_ACCOUNT_DELAY = 3

_sem = asyncio.Semaphore(1)
_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


def _sign(form_str: str) -> str:
    return hashlib.md5((form_str + REDEEM_SECRET).encode()).hexdigest()


def _is_rate_limited(exc: Exception) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429


async def _login(client: httpx.AsyncClient, player_id: str, api_base: str) -> dict:
    ts = int(time.time() * 1000)
    form_str = f"fid={player_id}&time={ts}"
    body = f"sign={_sign(form_str)}&{form_str}"
    response = await client.post(f"{api_base}/player", headers=_HEADERS, data=body, timeout=30.0)
    response.raise_for_status()
    return response.json()


async def fetch_player_info(player_id: str, api_base: str) -> dict:
    async with httpx.AsyncClient() as client:
        result = await _login(client, player_id, api_base)
    print("RAW RESULT:", result)

    if result.get("code") != 0:
        raise ValueError(result.get("msg", "Player not found"))

    return result["data"]


async def redeem_code(client: httpx.AsyncClient, player_id: str, code: str, api_base: str) -> dict:
    await _login(client, player_id, api_base)

    ts = int(time.time() * 1000)
    form_str = f"captcha_code=&cdk={code}&fid={player_id}&time={ts}"
    body = f"sign={_sign(form_str)}&{form_str}"

    response = await client.post(f"{api_base}/gift_code", headers=_HEADERS, data=body, timeout=30.0)
    response.raise_for_status()
    return response.json()


def is_success(response: dict) -> bool:
    if response.get('code') == 0:
        return True
    msg = response.get('msg', '').lower()
    return any(k in msg for k in ('success', 'claimed', 'redeemed'))


def is_already_redeemed(response: dict) -> bool:
    msg = response.get('msg', '').lower()
    return any(k in msg for k in ('already', 'used', 'duplicate', 'received'))


def is_permanent_failure(response: dict) -> bool:
    msg = response.get('msg', '').lower()
    return any(k in msg for k in ('time error', 'same type', 'expired', 'invalid', 'not exist'))


async def _redeem_account(client: httpx.AsyncClient, code: str, player_id: str, naam: str) -> None:
    async with _sem:
        try:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                try:
                    resp = await redeem_code(client, player_id, code, REDEEM_API)

                    if is_success(resp) or is_already_redeemed(resp):
                        await database.save_attempt(code, player_id, 'success', attempt)
                        logger.info("[%s] %s (%s) — success on attempt %d", code, naam, player_id, attempt)
                        return

                    msg = resp.get('msg', '')
                    if attempt < MAX_ATTEMPTS and not is_permanent_failure(resp):
                        logger.warning(
                            "[%s] %s (%s) — attempt %d failed (%s), retrying...",
                            code, naam, player_id, attempt, msg,
                        )
                        await asyncio.sleep(RETRY_BACKOFF)
                    else:
                        await database.save_attempt(code, player_id, 'failed', attempt, msg)
                        logger.error(
                            "[%s] %s (%s) — failed after %d attempts: %s",
                            code, naam, player_id, attempt, msg,
                        )
                        return

                except Exception as exc:
                    if attempt < MAX_ATTEMPTS:
                        backoff = RATE_LIMIT_BACKOFF if _is_rate_limited(exc) else RETRY_BACKOFF
                        logger.warning(
                            "[%s] %s (%s) — attempt %d error (%s), retrying in %ds...",
                            code, naam, player_id, attempt, exc, backoff,
                        )
                        await asyncio.sleep(backoff)
                    else:
                        await database.save_attempt(code, player_id, 'error', attempt, str(exc))
                        logger.error(
                            "[%s] %s (%s) — error after %d attempts: %s",
                            code, naam, player_id, attempt, exc,
                        )
        finally:
            await asyncio.sleep(INTER_ACCOUNT_DELAY)


async def redeem_all(code: str) -> None:
    await database.cleanup_old_attempts(days=3)
    async with httpx.AsyncClient() as client:
        accounts = await database.get_accounts_to_redeem(code)
        if not accounts:
            logger.info("[%s] No accounts to redeem for.", code)
            return
        logger.info("[%s] Redeeming for %d account(s)...", code, len(accounts))
        await asyncio.gather(
            *[_redeem_account(client, code, acc['player_id'], acc['name']) for acc in accounts]
        )
