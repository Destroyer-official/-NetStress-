"""
Performance Optimization Module

This module provides:
- REAL kernel optimizations (sysctl, socket options)
- REAL zero-copy networking (sendfile, MSG_ZEROCOPY)
- Honest capability reporting

NOTE: XDP, eBPF, and DPDK are NOT implemented.
For those, use external tools like xdp-tools, bcc, or DPDK.
"""

# Legacy imports (may contain simulations - use real_* modules instead)
try:
    from .kernel_optimizations import KernelOptimizer
    from .hardware_acceleration import HardwareAccelerator
    from .zero_copy import ZeroCopyEngine
    from .performance_validator import PerformanceValidator
except ImportError:
    KernelOptimizer = None
    HardwareAccelerator = None
    ZeroCopyEngine = None
    PerformanceValidator = None

# REAL implementations (no simulations)
try:
    from .real_kernel_opts import RealKernelOptimizer, get_optimizer, CapabilityReport
    from .real_zero_copy import RealZeroCopy, get_zero_copy, ZeroCopyStatus
except ImportError:
    RealKernelOptimizer = None
    RealZeroCopy = None

__all__ = [
    # Legacy (may have simulations)
    'KernelOptimizer',
    'HardwareAccelerator', 
    'ZeroCopyEngine',
    'PerformanceValidator',
    # Real implementations (recommended)
    'RealKernelOptimizer',
    'RealZeroCopy',
    'get_optimizer',
    'get_zero_copy',
    'CapabilityReport',
    'ZeroCopyStatus',
]