"""Travel AI Agent — HTTP API for n8n integration."""

from aiohttp import web
from src.api import create_app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)
