# AutoRedeemGifts_v4

## Architecture
This is an async Python daemon that polls for gift codes and redeems them across multiple game accounts.

**Flow:**
run.py → poller.py (15-min polling loop)
            ↓
  Fetch codes from GIFT_CODE_API → save to DB
            ↓
  For each new code: query eligible accounts (non-blacklisted, not yet redeemed)
            ↓
  Async tasks with semaphore (concurrency = 1) → redeemer.py
            ↓
  Retry up to 2 attempts (5-sec backoff) → log result to DB
