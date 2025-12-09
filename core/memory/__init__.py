"""
Advanced memory management system for the DDoS Testing Framework.
Provides memory pools, lock-free data structures, and garbage collection optimization.
"""

from .pool_manager import MemoryPoolManager, PacketBufferPool
from .lockfree import LockFreeQueue, LockFreeStack, LockFreeCounter, AtomicReference
from .gc_optimizer import GarbageCollectionOptimizer

__all__ = [
    'MemoryPoolManager', 'PacketBufferPool',
    'LockFreeQueue', 'LockFreeStack', 'LockFreeCounter', 'AtomicReference',
    'GarbageCollectionOptimizer'
]