"""Collect recent posts from public Telegram channels using Telethon."""

import json
import os
from datetime import datetime, timedelta, timezone

import yaml
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
CHANNELS_FILE = "channels.yml"


def load_channels() -> list[str]:
    with open(CHANNELS_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("channels", [])


async def collect_posts(client: TelegramClient, hours: int = 1) -> list[dict]:
    channels = load_channels()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    collected: list[dict] = []

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
                post = {
                    "channel": username,
                    "id": msg.id,
                    "date": msg.date.isoformat(),
                    "text": msg.text or "",
                }
                collected.append(post)
        except FloodWaitError as e:
            print(f"[WARN] rate limit while reading @{username}: wait {e.seconds}s")
            continue

    return collected


async def run_collector():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()

    print(f"[{datetime.now(timezone.utc).isoformat()}] collecting posts...")
    posts = await collect_posts(client)

    if posts:
        for post in posts:
            print(json.dumps(post, ensure_ascii=False))
        print(f"[INFO] collected {len(posts)} posts")
    else:
        print("[INFO] no new posts")

    await client.disconnect()
