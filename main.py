import os
import threading

import uvicorn

from admin.api import create_api
from bot.handler import create_bot
from core.cache import FileCache
from core.stats import BotStats


def _sync_proxy_env() -> None:
    for var in ("http_proxy", "https_proxy"):
        upper = var.upper()
        if not os.environ.get(var) and os.environ.get(upper):
            os.environ[var] = os.environ[upper]


def main() -> None:
    _sync_proxy_env()
    token = os.environ["BOT_TOKEN"]
    cache = FileCache(
        cache_dir=os.environ.get("CACHE_DIR", "/tmp/pdf_cache"),
        max_size_bytes=int(os.environ.get("CACHE_MAX_MB", "500")) * 1024 * 1024,
    )
    stats = BotStats()
    bot = create_bot(token, cache, stats)
    api = create_api(cache, stats)

    bot_thread = threading.Thread(target=bot.infinity_polling, daemon=True)
    bot_thread.start()
    print("Bot started")

    uvicorn.run(
        api,
        host="0.0.0.0",
        port=int(os.environ.get("API_PORT", "8000")),
        log_level="warning",
    )


if __name__ == "__main__":
    main()
