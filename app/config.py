import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

_env = os.environ.get('APP_ENV', '').strip()
if _env:
    _override_file = BASE_DIR / f'.env.{_env}'
    if _override_file.exists():
        load_dotenv(_override_file, override=True)

def _require(key: str) -> str:
    val = os.environ.get(key, '').strip()
    if not val:
        raise RuntimeError(f"{key} is not set in .env")
    return val

def _optional(key: str, default: str) -> str:
    return os.environ.get(key, default).strip()

# Verplichte variabelen
GIFT_CODE_API   = _require('GIFT_CODE_API')
REDEEM_SECRET   = _require('REDEEM_SECRET')
JWT_SECRET      = _require('JWT_SECRET')
MOD_PASSWORD    = _require('MOD_PASSWORD')

# Optionele variabelen met fallback
REDEEM_API      = _optional('REDEEM_API', 'https://kingshot-giftcode.centurygame.com/api')
DB_PATH         = Path(_optional('DB_PATH', str(BASE_DIR / 'data' / 'autoredeemgifts.db')))
ALLOWED_ORIGINS = _optional('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')