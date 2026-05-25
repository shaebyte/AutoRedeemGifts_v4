import hashlib
import time
import httpx

from app.config import REDEEM_SECRET

_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}


def _sign(form_str: str) -> str:
    return hashlib.md5((form_str + REDEEM_SECRET).encode()).hexdigest()


async def _login(client: httpx.AsyncClient, player_id: str, api_base: str) -> None:
    ts = int(time.time() * 1000)
    form_str = f"fid={player_id}&time={ts}"
    body = f"sign={_sign(form_str)}&{form_str}"
    response = await client.post(f"{api_base}/player", headers=_HEADERS, data=body, timeout=30.0)
    response.raise_for_status()
    return response.json()

async def fetch_player_info(player_id: str, api_base: str) -> dict:
    """Validates that a player_id exists and returns game data."""
    async with httpx.AsyncClient() as client:
        result = await _login(client, player_id, api_base)
    print("RAW RESULT:", result)

    if result.get("code") != 0:
        raise ValueError(result.get("msg", "Player not found"))

    return result["data"]  # fid, nickname, kid, stove_lv, avatar_image

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
    """Returns True for errors that won't resolve on retry."""
    msg = response.get('msg', '').lower()
    return any(k in msg for k in ('time error', 'same type', 'expired', 'invalid', 'not exist'))
