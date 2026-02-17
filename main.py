"""Travel AI Agent — entry point."""

import asyncio
from datetime import datetime, timedelta, timezone

from src.collector import run_collector, run_daily_collector

INTERVAL = 3600  # seconds
MSK = timezone(timedelta(hours=3))
DAILY_HOUR = 1  # 01:00 MSK


def seconds_until_next_run() -> float:
    now = datetime.now(MSK)
    target = now.replace(hour=DAILY_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def hourly_loop():
    while True:
        try:
            await run_collector()
        except Exception as e:
            print(f"[ERROR] collector failed: {e}")
        await asyncio.sleep(INTERVAL)


async def daily_loop():
    while True:
        wait = seconds_until_next_run()
        print(f"[INFO] daily collector: next run in {wait:.0f}s")
        await asyncio.sleep(wait)
        try:
            await run_daily_collector()
        except Exception as e:
            print(f"[ERROR] daily collector failed: {e}")


async def main():
    await asyncio.gather(hourly_loop(), daily_loop())


if __name__ == "__main__":
    asyncio.run(main())
