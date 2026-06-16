import threading
import time


class BotStats:
    def __init__(self):
        self._lock = threading.Lock()
        self.started_at = time.time()
        self.conversions_total = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_hit(self):
        with self._lock:
            self.cache_hits += 1

    def record_miss(self):
        with self._lock:
            self.cache_misses += 1
            self.conversions_total += 1

    def to_dict(self) -> dict:
        return {
            "uptime_seconds": int(time.time() - self.started_at),
            "conversions_total": self.conversions_total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }
