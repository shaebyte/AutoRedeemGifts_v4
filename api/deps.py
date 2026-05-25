import sys
from pathlib import Path

# Zorgt dat 'app.config' vindbaar is vanuit de projectroot
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiosqlite
from app.config import DB_PATH


async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        yield db
