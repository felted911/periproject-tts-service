# Tests for cache manager
import pytest
import asyncio
from src.tts_service.infrastructure import CacheManager


@pytest.mark.asyncio
async def test_cache_set_get(cache_manager):
    """Test setting and getting items from cache."""
    # Set item
    key = "test:key"
    data = b"test data"
    result = await cache_manager.set(key, data)
    assert result is True

    # Get item
    cached_data = await cache_manager.get(key)
    assert cached_data == data


@pytest.mark.asyncio
async def test_cache_delete(cache_manager):
    """Test deleting items from cache."""
    # Set item
    key = "test:key"
    data = b"test data"
    await cache_manager.set(key, data)

    # Delete item
    result = await cache_manager.delete(key)
    assert result is True

    # Try to get deleted item
    cached_data = await cache_manager.get(key)
    assert cached_data is None

    # Try to delete non-existent item
    result = await cache_manager.delete("non:existent")
    assert result is False


@pytest.mark.asyncio
async def test_cache_clear(cache_manager):
    """Test clearing cache."""
    # Set items
    await cache_manager.set("key1", b"data1")
    await cache_manager.set("key2", b"data2")

    # Clear cache
    result = await cache_manager.clear()
    assert result is True

    # Try to get items
    assert await cache_manager.get("key1") is None
    assert await cache_manager.get("key2") is None


@pytest.mark.asyncio
async def test_cache_stats(cache_manager):
    """Test getting cache statistics."""
    # Set items
    await cache_manager.set("key1", b"data1")
    await cache_manager.set("key2", b"data2" * 100)  # Larger item

    # Get stats
    stats = await cache_manager.get_stats()

    # Check stats
    assert stats["enabled"] is True
    assert stats["count"] == 2
    assert stats["size"] > 0
    assert stats["max_size"] > 0


@pytest.mark.asyncio
async def test_cache_expiration(cache_manager):
    """Test cache item expiration."""
    # Create cache with short TTL
    short_ttl_cache = CacheManager(
        cache_dir=cache_manager._cache_dir,
        enabled=True,
        ttl=1,  # 1 second TTL
        max_size=1024 * 1024,
    )
    # For compatibility with existing tests
    short_ttl_cache._cache_dir = cache_manager._cache_dir

    # Set item
    key = "test:expiration"
    data = b"test data"
    await short_ttl_cache.set(key, data)

    # Verify item is there
    assert await short_ttl_cache.get(key) == data

    # Wait for TTL to expire
    await asyncio.sleep(1.1)

    # Item should be gone
    assert await short_ttl_cache.get(key) is None


@pytest.mark.asyncio
async def test_cache_ensure_size(cache_manager):
    """Test cache size management."""
    # Create cache with small max size
    small_cache = CacheManager(
        cache_dir=cache_manager._cache_dir,
        enabled=True,
        ttl=3600,
        max_size=100,  # Very small cache
    )
    # For compatibility with existing tests
    small_cache._cache_dir = cache_manager._cache_dir

    # Set small item
    await small_cache.set("key1", b"data1")

    # Set larger item to trigger eviction
    await small_cache.set("key2", b"data2" * 50)

    # First item should be evicted
    assert await small_cache.get("key1") is None
    assert await small_cache.get("key2") is not None


@pytest.mark.asyncio
async def test_cache_disabled(cache_manager):
    """Test disabled cache."""
    # Create disabled cache
    disabled_cache = CacheManager(
        cache_dir=cache_manager._cache_dir,
        enabled=False,
        ttl=3600,
        max_size=1024 * 1024,
    )
    # For compatibility with existing tests
    disabled_cache._cache_dir = cache_manager._cache_dir

    # Set item
    result = await disabled_cache.set("key", b"data")
    assert result is False

    # Get item
    cached_data = await disabled_cache.get("key")
    assert cached_data is None

    # Delete item
    result = await disabled_cache.delete("key")
    assert result is False

    # Clear cache
    result = await disabled_cache.clear()
    assert result is False

    # Get stats
    stats = await disabled_cache.get_stats()
    assert stats["enabled"] is False
    assert stats["count"] == 0
