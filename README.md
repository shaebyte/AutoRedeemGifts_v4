# AutoRedeemGifts_v4

## Architecture
This is an async Python daemon that polls for gift codes and redeems them across multiple game accounts.

**Flow:**
1. run.py → poller.py (15-min polling loop)
2. Fetch codes from GIFT_CODE_API → save to DB
3. For each new code: query eligible accounts (non-blacklisted, not yet redeemed)
4. Async tasks with semaphore (concurrency = 1) → redeemer.py
5. Retry up to 2 attempts (5-sec backoff) → log result to DB
