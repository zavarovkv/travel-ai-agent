"""HTTP API server — triggered by n8n workflows."""

import os
from datetime import datetime, timezone

from aiohttp import web
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from src.collector import API_ID, API_HASH, SESSION_PATH, collect_messages


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "time": datetime.now(timezone.utc).isoformat()})


async def handle_collect(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)

    channels = body.get("channels", [])
    hours = int(body.get("hours", 1))

    if not channels:
        return web.json_response([])

    client: TelegramClient = request.app["client"]

    # Reconnect if session dropped
    if not client.is_connected():
        await client.connect()

    messages = await collect_messages(client, channels, hours)

    posts = [
        {
            "channel": getattr(msg.chat, "username", None),
            "id": msg.id,
            "date": msg.date.isoformat(),
            "text": msg.text or "",
            "has_media": isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)),
        }
        for msg in messages
    ]

    print(f"[{datetime.now(timezone.utc).isoformat()}] /collect channels={channels} hours={hours} → {len(posts)} posts")
    return web.json_response(posts)


async def on_startup(app: web.Application) -> None:
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()
    app["client"] = client
    print("[INFO] Telethon client started")


async def on_shutdown(app: web.Application) -> None:
    client = app.get("client")
    if client:
        await client.disconnect()
        print("[INFO] Telethon client disconnected")


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", handle_health)
    app.router.add_post("/collect", handle_collect)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app
