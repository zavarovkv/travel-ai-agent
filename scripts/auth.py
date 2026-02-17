"""Interactive Telethon auth — run once to create session file.

Usage:
    docker compose run -it app python scripts/auth.py
"""

import os

from telethon import TelegramClient

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION_PATH = os.path.join("sessions", "collector")


async def main():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"Authorized as {me.first_name} (id={me.id})")
    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
