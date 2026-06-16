import time

import pytest

from core.cache import FileCache


@pytest.fixture
def cache(tmp_path):
    return FileCache(str(tmp_path), max_size_bytes=100)


class TestGet:
    def test_miss_returns_none(self, cache):
        assert cache.get("missing") is None

    def test_hit_returns_path(self, cache):
        cache.put("a", b"x" * 10)
        assert cache.get("a") is not None

    def test_hit_updates_mtime(self, cache):
        cache.put("a", b"x" * 10)
        p = cache.get("a")
        mtime_before = p.stat().st_mtime
        time.sleep(0.05)
        cache.get("a")
        assert p.stat().st_mtime > mtime_before


class TestPut:
    def test_returns_path_to_pdf(self, cache):
        p = cache.put("a", b"data")
        assert p.exists()
        assert p.suffix == ".pdf"

    def test_stored_data_is_correct(self, cache):
        data = b"pdf content"
        p = cache.put("a", data)
        assert p.read_bytes() == data

    def test_overwrites_existing(self, cache):
        cache.put("a", b"old")
        p = cache.put("a", b"new")
        assert p.read_bytes() == b"new"


class TestEviction:
    def test_no_eviction_within_limit(self, cache):
        cache.put("a", b"x" * 40)
        cache.put("b", b"x" * 40)
        assert cache.get("a") is not None
        assert cache.get("b") is not None

    def test_evicts_oldest_when_over_limit(self, cache):
        cache.put("a", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", b"x" * 40)
        time.sleep(0.05)
        cache.put("c", b"x" * 40)  # total 120 > 100, "a" должен вылететь

        assert cache.get("a") is None
        assert cache.get("b") is not None
        assert cache.get("c") is not None

    def test_evicts_multiple_files_if_needed(self, cache):
        cache.put("a", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", b"x" * 40)
        time.sleep(0.05)
        cache.put("c", b"x" * 90)  # вытесняет и "a" и "b"

        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is not None

    def test_get_promotes_file_in_lru(self, cache):
        cache.put("a", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", b"x" * 40)
        time.sleep(0.05)
        cache.get("a")  # "a" становится новее "b"
        time.sleep(0.05)
        cache.put("c", b"x" * 40)  # "b" должен вылететь, не "a"

        assert cache.get("b") is None
        assert cache.get("a") is not None
        assert cache.get("c") is not None
