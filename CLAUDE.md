# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Initialize the database (first-time setup)
python scripts/create_db.py

# Start the poller daemon
python run.py
```

## Configuration

Copy `.env.example` to `.env` (or create `.env` directly) with:
- `GIFT_CODE_API` — URL to fetch new gift codes (required)
- `REDEEM_SECRET` — Secret used to sign API requests via MD5 (required)
- `REDEEM_API` — Redeem endpoint URL (optional, has default)

Database is stored at `data/autoredeemgifts.db`.

## Architecture

This is an async Python daemon that polls for gift codes and redeems them across multiple game accounts.

**Flow:**

```
run.py → poller.py (15-min polling loop)
            ↓
  Fetch codes from GIFT_CODE_API → save to DB
            ↓
  For each new code: query eligible accounts (non-blacklisted, not yet redeemed)
            ↓
  Async tasks with semaphore (concurrency = 1) → redeemer.py
            ↓
  Retry up to 2 attempts (5-sec backoff) → log result to DB
```

**Key files:**

- [app/poller.py](app/poller.py) — Orchestrator: polling loop, task dispatch, retry logic
- [app/redeemer.py](app/redeemer.py) — HTTP redemption logic: login → redeem, MD5 request signing
- [app/database.py](app/database.py) — All async SQLite operations (aiosqlite)
- [app/config.py](app/config.py) — Loads and validates env vars, defines paths

**Database schema** (created by `scripts/create_db.py`):
- `gift_codes` — unique codes with timestamps
- `accounts` — player accounts with `blacklisted` flag
- `redeem_attempts` — per-(code, player_id) attempt tracking with status and error messages; UNIQUE constraint prevents double-redeem

**Redemption API signing:** `redeemer.py` signs requests as `MD5(form_data_string + REDEEM_SECRET)`. Responses are parsed to distinguish success, already-redeemed, and error states.
