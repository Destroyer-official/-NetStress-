"""
Advanced Evasion Module

Provides traffic shaping, protocol obfuscation, and timing pattern
manipulation for evading basic detection systems.

WARNING: For authorized security testing only.
"""

from .traffic_shaping import TrafficShaper, ShapingProfile, ShapingConfig, AdaptiveShaper
from .protocol_obfuscation import ProtocolObfuscator, ObfuscationMethod, ObfuscationConfig
from .timing_patterns import TimingController, TimingPattern, TimingConfig

__all__ = [
    'TrafficShaper',
    'ShapingProfile',
    'ShapingConfig',
    'AdaptiveShaper',
    'ProtocolObfuscator',
    'ObfuscationMethod',
    'ObfuscationConfig',
    'TimingController',
    'TimingPattern',
    'TimingConfig',
]
