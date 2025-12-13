# Core module initialization
"""
NetStress Core Module - Power Trio Architecture

Provides the core functionality for network stress testing:
- Native high-performance engine (Rust/C with Python fallback)
- Advanced attack vectors and orchestration
- AI-driven optimization
- Evasion techniques
- Reconnaissance capabilities
- Anti-detection features
- Distributed testing coordination
- Real-time intelligence
"""

# Native Engine (high-performance Rust/C with Python fallback)
from .native_engine import (
    NativePacketEngine,
    EngineConfig,
    EngineStats,
    EngineBackend,
    start_flood,
    build_packet,
    get_capabilities,
    is_native_available,
)

# Version info
__version__ = "2.0.0"
__codename__ = "Power Trio"

__all__ = [
    # Native Engine
    'NativePacketEngine',
    'EngineConfig',
    'EngineStats',
    'EngineBackend',
    'start_flood',
    'build_packet',
    'get_capabilities',
    'is_native_available',
    # Version
    '__version__',
    '__codename__',
]