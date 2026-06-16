from fastapi import FastAPI

from core.cache import FileCache
from core.stats import BotStats


def create_api(cache: FileCache, stats: BotStats) -> FastAPI:
    app = FastAPI(title="PDF Bot Admin")

    @app.get("/api/cache/stats")
    def cache_stats():
        files = list(cache._dir.iterdir())
        total_size = sum(f.stat().st_size for f in files)
        return {
            "files": len(files),
            "size_bytes": total_size,
            "size_mb": round(total_size / 1024 / 1024, 2),
            "max_size_mb": round(cache._max_size / 1024 / 1024, 2),
            "fill_pct": round(total_size / cache._max_size * 100, 1) if cache._max_size else 0,
        }

    @app.delete("/api/cache")
    def cache_clear():
        for f in cache._dir.iterdir():
            f.unlink()
        return {"cleared": True}

    @app.get("/api/bot/status")
    def bot_status():
        return {"status": "online", **stats.to_dict()}

    return app
