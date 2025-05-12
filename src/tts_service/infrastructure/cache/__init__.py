"""Cache package for TTS service.

This package provides caching functionality for the TTS service, including:
- Cache manager for high-level cache operations
- File storage for storing cached data
- Metadata management for tracking cache item information
- Eviction policies for managing cache size
"""

from .protocols import CacheManagerProtocol, CacheStorageProtocol, CacheMetadataProtocol, EvictionPolicyProtocol
from .cache_manager import CacheManager
from .file_storage import FileStorage
from .metadata_manager import MetadataManager
from .eviction_policy import LRUEvictionPolicy, FIFOEvictionPolicy

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
