import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

GIFT_CODE_API: str = os.environ.get('GIFT_CODE_API', '')
if not GIFT_CODE_API:
    raise RuntimeError("GIFT_CODE_API not set in .env")

REDEEM_SECRET: str = os.environ.get('REDEEM_SECRET', '')
if not REDEEM_SECRET:
    raise RuntimeError("REDEEM_SECRET not set in .env")

REDEEM_API: str = os.environ.get('REDEEM_API', 'https://kingshot-giftcode.centurygame.com/api')

DB_PATH: Path = Path(os.environ.get('DB_PATH', str(BASE_DIR / 'data' / 'autoredeemgifts.db')))
