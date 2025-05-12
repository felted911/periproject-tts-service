"""Cache module for the TTS service.

This module provides caching functionality for the TTS service. It has been
refactored to follow better design principles, with main components split
into a dedicated cache package.
"""

from .cache.protocols import (
    CacheManagerProtocol, CacheStorageProtocol, 
    CacheMetadataProtocol, EvictionPolicyProtocol
)
from .cache.cache_manager import CacheManager
from .cache.file_storage import FileStorage
from .cache.metadata_manager import MetadataManager
from .cache.eviction_policy import LRUEvictionPolicy, FIFOEvictionPolicy

# Re-export components for backward compatibility
__all__ = [
    'CacheManagerProtocol',
    'CacheStorageProtocol', 
    'CacheMetadataProtocol',
    'EvictionPolicyProtocol',
    'CacheManager',
    'FileStorage',
    'MetadataManager',
    'LRUEvictionPolicy',
    'FIFOEvictionPolicy',
]
