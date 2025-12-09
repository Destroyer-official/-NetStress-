"""
Core platform abstraction module for the Advanced DDoS Testing Framework.
Provides cross-platform compatibility and platform-specific optimizations.
"""

from .detection import PlatformDetector
from .abstraction import (
    PlatformEngine, 
    PlatformAbstraction,
    PlatformAdapter,
    WindowsAdapter, 
    LinuxAdapter, 
    MacOSAdapter,
    SocketConfig,
    SystemInfo
)
from .capabilities import CapabilityMapper

__all__ = [
    'PlatformDetector', 
    'PlatformEngine', 
    'PlatformAbstraction',
    'PlatformAdapter',
    'WindowsAdapter',
    'LinuxAdapter',
    'MacOSAdapter',
    'SocketConfig',
    'SystemInfo',
    'CapabilityMapper'
]