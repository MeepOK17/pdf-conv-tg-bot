import time

import pytest

from core.cache import FileCache, sha256


@pytest.fixture
def cache(tmp_path):
    return FileCache(str(tmp_path), max_size_bytes=100)


class TestSha256:
    def test_same_data_same_hash(self):
        assert sha256(b"abc") == sha256(b"abc")

    def test_different_data_different_hash(self):
        assert sha256(b"abc") != sha256(b"xyz")


class TestGetById:
    def test_miss_returns_none(self, cache):
        assert cache.get_by_id("unknown") is None

    def test_hit_returns_path(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        assert cache.get_by_id("uid1") is not None

    def test_stale_ref_returns_none(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        (cache._dir / "hash1.pdf").unlink()
        assert cache.get_by_id("uid1") is None

    def test_hit_updates_mtime(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        p = cache.get_by_id("uid1")
        mtime_before = p.stat().st_mtime
        time.sleep(0.05)
        cache.get_by_id("uid1")
        assert p.stat().st_mtime > mtime_before


class TestGetByHash:
    def test_miss_returns_none(self, cache):
        assert cache.get_by_hash("deadbeef") is None

    def test_hit_returns_path(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        assert cache.get_by_hash("hash1") is not None

    def test_hit_updates_mtime(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        p = cache.get_by_hash("hash1")
        mtime_before = p.stat().st_mtime
        time.sleep(0.05)
        cache.get_by_hash("hash1")
        assert p.stat().st_mtime > mtime_before


class TestLinkId:
    def test_links_new_id_to_existing_hash(self, cache):
        cache.put("uid1", "hash1", b"x" * 10)
        cache.link_id("uid2", "hash1")
        assert cache.get_by_id("uid2") is not None

    def test_linked_id_resolves_same_pdf(self, cache):
        cache.put("uid1", "hash1", b"pdf data")
        cache.link_id("uid2", "hash1")
        assert cache.get_by_id("uid2").read_bytes() == b"pdf data"


class TestPut:
    def test_returns_pdf_path(self, cache):
        p = cache.put("uid1", "hash1", b"data")
        assert p.exists() and p.suffix == ".pdf"

    def test_creates_ref_file(self, cache):
        cache.put("uid1", "hash1", b"data")
        ref = cache._dir / "uid1.ref"
        assert ref.exists()
        assert ref.read_text() == "hash1"

    def test_stored_data_is_correct(self, cache):
        p = cache.put("uid1", "hash1", b"pdf content")
        assert p.read_bytes() == b"pdf content"


class TestEviction:
    def test_no_eviction_within_limit(self, cache):
        cache.put("a", "ha", b"x" * 40)
        cache.put("b", "hb", b"x" * 40)
        assert cache.get_by_hash("ha") is not None
        assert cache.get_by_hash("hb") is not None

    def test_evicts_oldest_when_over_limit(self, cache):
        cache.put("a", "ha", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", "hb", b"x" * 40)
        time.sleep(0.05)
        cache.put("c", "hc", b"x" * 40)

        assert cache.get_by_hash("ha") is None
        assert cache.get_by_hash("hb") is not None
        assert cache.get_by_hash("hc") is not None

    def test_ref_files_not_counted_in_size(self, cache):
        cache.put("a", "ha", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", "hb", b"x" * 40)
        assert cache.get_by_id("a") is not None
        assert cache.get_by_id("b") is not None

    def test_get_by_hash_promotes_lru(self, cache):
        cache.put("a", "ha", b"x" * 40)
        time.sleep(0.05)
        cache.put("b", "hb", b"x" * 40)
        time.sleep(0.05)
        cache.get_by_hash("ha")
        time.sleep(0.05)
        cache.put("c", "hc", b"x" * 40)

        assert cache.get_by_hash("hb") is None
        assert cache.get_by_hash("ha") is not None
        assert cache.get_by_hash("hc") is not None
