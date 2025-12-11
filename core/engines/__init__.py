"""
Real Packet Engines Module

This module provides actual high-performance packet generation.
No simulations - every packet is really sent.
"""

from .real_packet_engine import (
    RealPacketEngine,
    RealPerformanceMonitor,
    PacketStats,
    SocketOptimizationResult,
    create_engine
)

__all__ = [
    'RealPacketEngine',
    'RealPerformanceMonitor', 
    'PacketStats',
    'SocketOptimizationResult',
    'create_engine'
]
