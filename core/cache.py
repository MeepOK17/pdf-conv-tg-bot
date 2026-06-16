from pathlib import Path
from typing import Optional


class FileCache:
    def __init__(self, cache_dir: str, max_size_bytes: int = 500 * 1024 * 1024):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_size = max_size_bytes

    def get(self, key: str) -> Optional[Path]:
        p = self._dir / f"{key}.pdf"
        if p.exists():
            p.touch()  # обновляем mtime для LRU
            return p
        return None

    def put(self, key: str, data: bytes) -> Path:
        p = self._dir / f"{key}.pdf"
        p.write_bytes(data)
        self._evict()
        return p

    def _evict(self) -> None:
        files = sorted(self._dir.iterdir(), key=lambda f: f.stat().st_mtime)
        total = sum(f.stat().st_size for f in files)
        for f in files:
            if total <= self._max_size:
                break
            total -= f.stat().st_size
            f.unlink()
