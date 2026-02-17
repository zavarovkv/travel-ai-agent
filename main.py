"""Travel AI Agent — entry point."""

import asyncio

from src.collector import run_collector

INTERVAL = 3600  # seconds


async def main():
    while True:
        try:
            await run_collector()
        except Exception as e:
            print(f"[ERROR] collector failed: {e}")
        await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
