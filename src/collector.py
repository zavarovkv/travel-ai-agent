"""Collect recent posts from public Telegram channels."""

import os
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
)

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION_PATH = os.path.join("sessions", "collector")


async def collect_messages(client: TelegramClient, channels: list[str], hours: int = 1):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    messages = []

    for username in channels:
        try:
            entity = await client.get_entity(username)
        except (
            UsernameNotOccupiedError,
            UsernameInvalidError,
            ChannelInvalidError,
            ChannelPrivateError,
            ValueError,
        ) as e:
            print(f"[WARN] channel @{username}: {e}")
            continue
        except FloodWaitError as e:
            print(f"[WARN] rate limit: wait {e.seconds}s, skipping @{username}")
            continue

        try:
            async for msg in client.iter_messages(entity, offset_date=since, reverse=True):
                if msg.date < since:
                    continue
                messages.append(msg)
        except FloodWaitError as e:
            print(f"[WARN] rate limit while reading @{username}: wait {e.seconds}s")
            continue

    return messages
