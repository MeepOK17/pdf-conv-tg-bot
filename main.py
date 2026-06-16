import os

from bot.handler import create_bot


def _sync_proxy_env() -> None:
    for var in ("http_proxy", "https_proxy"):
        upper = var.upper()
        if not os.environ.get(var) and os.environ.get(upper):
            os.environ[var] = os.environ[upper]


def main() -> None:
    _sync_proxy_env()
    token = os.environ["BOT_TOKEN"]
    bot = create_bot(token)
    print("Bot started")
    bot.infinity_polling()


if __name__ == "__main__":
    main()
