"""Collect recent posts from public Telegram channels and forward to target."""

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


def load_config() -> dict:
    with open(CHANNELS_FILE) as f:
        return yaml.safe_load(f)


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


async def publish(client: TelegramClient, messages, target: str):
    target_entity = await client.get_entity(target)
    forwarded = 0
    for msg in messages:
        try:
            await client.forward_messages(target_entity, msg)
            forwarded += 1
        except Exception as e:
            print(f"[WARN] failed to forward msg {msg.id}: {e}")
    return forwarded


async def run_collector():
    config = load_config()
    channels = config.get("channels", [])
    target = config.get("target")

    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()

    print(f"[{datetime.now(timezone.utc).isoformat()}] collecting posts...")
    messages = await collect_messages(client, channels)

    if messages:
        for msg in messages:
            post = {
                "channel": getattr(msg.chat, "username", None),
                "id": msg.id,
                "date": msg.date.isoformat(),
                "text": msg.text or "",
            }
            print(json.dumps(post, ensure_ascii=False))

        if target:
            forwarded = await publish(client, messages, target)
            print(f"[INFO] forwarded {forwarded}/{len(messages)} posts to @{target}")
        else:
            print(f"[INFO] collected {len(messages)} posts (no target channel set)")
    else:
        print("[INFO] no new posts")

    await client.disconnect()
