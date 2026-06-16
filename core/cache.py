import hashlib
from pathlib import Path
from typing import Optional


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FileCache:
    def __init__(self, cache_dir: str, max_size_bytes: int = 500 * 1024 * 1024):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_size = max_size_bytes

    # --- lookup ---

    def get_by_id(self, unique_id: str) -> Optional[Path]:
        ref = self._dir / f"{unique_id}.ref"
        if not ref.exists():
            return None
        pdf = self._dir / f"{ref.read_text().strip()}.pdf"
        if pdf.exists():
            pdf.touch()
            return pdf
        ref.unlink()  # stale ref
        return None

    def get_by_hash(self, hash_key: str) -> Optional[Path]:
        pdf = self._dir / f"{hash_key}.pdf"
        if pdf.exists():
            pdf.touch()
            return pdf
        return None

    # --- store ---

    def put(self, unique_id: str, hash_key: str, data: bytes) -> Path:
        pdf = self._dir / f"{hash_key}.pdf"
        pdf.write_bytes(data)
        (self._dir / f"{unique_id}.ref").write_text(hash_key)
        self._evict()
        return pdf

    def link_id(self, unique_id: str, hash_key: str) -> None:
        """Привязать unique_id к уже существующему hash (hit по хэшу)."""
        (self._dir / f"{unique_id}.ref").write_text(hash_key)

    # --- eviction ---

    def _evict(self) -> None:
        pdfs = sorted(
            (f for f in self._dir.iterdir() if f.suffix == ".pdf"),
            key=lambda f: f.stat().st_mtime,
        )
        total = sum(f.stat().st_size for f in pdfs)
        for f in pdfs:
            if total <= self._max_size:
                break
            total -= f.stat().st_size
            f.unlink()
