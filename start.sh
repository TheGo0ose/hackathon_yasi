#!/bin/sh
# Start Telegram bot in the background
cd /app/tg_bot && python bot.py &

# Start FastAPI backend (foreground — keeps the container alive)
cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
