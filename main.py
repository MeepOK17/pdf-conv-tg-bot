import os

from bot.handler import create_bot
from core.cache import FileCache


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
    bot = create_bot(token, cache)
    print("Bot started")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
