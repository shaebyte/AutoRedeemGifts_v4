import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS gift_codes (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        code       TEXT    NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS accounts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id   TEXT    NOT NULL UNIQUE,
        name        TEXT    NOT NULL,
        blacklisted INTEGER NOT NULL DEFAULT 0,
        comments    TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS redeem_attempts (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        gift_code     TEXT    NOT NULL,
        player_id     TEXT    NOT NULL,
        status        TEXT    NOT NULL,
        attempt_count INTEGER NOT NULL DEFAULT 1,
        error_message TEXT,
        redeemed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (gift_code, player_id),
        FOREIGN KEY (gift_code)  REFERENCES gift_codes(code),
        FOREIGN KEY (player_id)  REFERENCES accounts(player_id)
    );
""")
conn.commit()
conn.close()
print(f"Database ready at {DB_PATH}")
