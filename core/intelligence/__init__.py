"""
Traffic Intelligence Module

Provides advanced traffic analysis and intelligence gathering:
- Deep packet inspection simulation
- Traffic pattern analysis
- Anomaly detection
- Protocol fingerprinting
"""

from .traffic_analysis import (
    TrafficType, AnomalyType, PacketInfo, FlowInfo, Anomaly,
    PacketAnalyzer, FlowTracker, AnomalyDetector,
    ProtocolFingerprinter, TrafficIntelligence
)

__all__ = [
    'TrafficType', 'AnomalyType', 'PacketInfo', 'FlowInfo', 'Anomaly',
    'PacketAnalyzer', 'FlowTracker', 'AnomalyDetector',
    'ProtocolFingerprinter', 'TrafficIntelligence',
]
