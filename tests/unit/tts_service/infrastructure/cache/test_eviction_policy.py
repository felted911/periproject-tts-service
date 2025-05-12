"""Tests for cache eviction policies."""

import pytest
from tts_service.infrastructure.cache.eviction_policy import LRUEvictionPolicy, FIFOEvictionPolicy


def test_lru_eviction_policy_no_eviction_needed():
    """Test LRU policy when no eviction is needed."""
    # Create LRU eviction policy
    policy = LRUEvictionPolicy()

    # Test metadata (current size = 300)
    metadata = {
        "key1": {"size": 100, "last_accessed": 1000},
        "key2": {"size": 200, "last_accessed": 1100},
    }

    # Test with enough space available
    required_space = 200
    max_size = 1000  # 1000 > 300 + 200

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify no items are evicted
    assert len(items_to_evict) == 0


def test_lru_eviction_policy_eviction_needed():
    """Test LRU policy when eviction is needed."""
    # Create LRU eviction policy
    policy = LRUEvictionPolicy()

    # Test metadata (current size = 300)
    metadata = {
        "key1": {"size": 100, "last_accessed": 1000},  # Oldest access time
        "key2": {"size": 200, "last_accessed": 1100},
    }

    # Test with not enough space available
    required_space = 800
    max_size = 1000  # 1000 < 300 + 800

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify key1 is evicted (oldest access time)
    assert len(items_to_evict) == 1
    assert items_to_evict[0] == "key1"


def test_lru_eviction_policy_multiple_items():
    """Test LRU policy when multiple items need to be evicted."""
    # Create LRU eviction policy
    policy = LRUEvictionPolicy()

    # Test metadata (current size = 600)
    metadata = {
        "key1": {"size": 100, "last_accessed": 1000},  # Oldest
        "key2": {"size": 200, "last_accessed": 1100},  # Second oldest
        "key3": {"size": 300, "last_accessed": 1200},  # Newest
    }

    # Test with not enough space available
    required_space = 700
    max_size = 1000  # 1000 < 600 + 700

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify key1 and key2 are evicted (oldest access times, total 300)
    assert len(items_to_evict) == 2
    assert "key1" in items_to_evict
    assert "key2" in items_to_evict
    assert "key3" not in items_to_evict


def test_fifo_eviction_policy_no_eviction_needed():
    """Test FIFO policy when no eviction is needed."""
    # Create FIFO eviction policy
    policy = FIFOEvictionPolicy()

    # Test metadata (current size = 300)
    metadata = {
        "key1": {"size": 100, "created_at": 1000},
        "key2": {"size": 200, "created_at": 1100},
    }

    # Test with enough space available
    required_space = 200
    max_size = 1000  # 1000 > 300 + 200

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify no items are evicted
    assert len(items_to_evict) == 0


def test_fifo_eviction_policy_eviction_needed():
    """Test FIFO policy when eviction is needed."""
    # Create FIFO eviction policy
    policy = FIFOEvictionPolicy()

    # Test metadata (current size = 300)
    metadata = {
        "key1": {"size": 100, "created_at": 1000},  # Oldest creation time
        "key2": {"size": 200, "created_at": 1100},
    }

    # Test with not enough space available
    required_space = 800
    max_size = 1000  # 1000 < 300 + 800

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify key1 is evicted (oldest creation time)
    assert len(items_to_evict) == 1
    assert items_to_evict[0] == "key1"


def test_fifo_eviction_policy_multiple_items():
    """Test FIFO policy when multiple items need to be evicted."""
    # Create FIFO eviction policy
    policy = FIFOEvictionPolicy()

    # Test metadata (current size = 600)
    metadata = {
        "key1": {"size": 100, "created_at": 1000},  # Oldest
        "key2": {"size": 200, "created_at": 1100},  # Second oldest
        "key3": {"size": 300, "created_at": 1200},  # Newest
    }

    # Test with not enough space available
    required_space = 700
    max_size = 1000  # 1000 < 600 + 700

    # Get items to evict
    items_to_evict = policy.get_items_to_evict(metadata, required_space, max_size)

    # Verify key1 and key2 are evicted (oldest creation times, total 300)
    assert len(items_to_evict) == 2
    assert "key1" in items_to_evict
    assert "key2" in items_to_evict
    assert "key3" not in items_to_evict
