"""
Bot configuration — loads settings from .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the tg_bot directory
load_dotenv(Path(__file__).resolve().parent / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
WEB_APP_URL: str = os.getenv("WEB_APP_URL", "https://example.com")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")
