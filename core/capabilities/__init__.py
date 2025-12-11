"""
Capability Reporting Module

Provides honest reporting of what features are actually available.
No false claims - only real capabilities are reported.
"""

from .capability_report import (
    CapabilityChecker,
    CapabilityReport,
    get_capabilities
)

__all__ = [
    'CapabilityChecker',
    'CapabilityReport',
    'get_capabilities'
]
