"""
Traffic Intelligence Module

Provides advanced traffic analysis and intelligence gathering:
- Deep packet inspection simulation
- Traffic pattern analysis
- Anomaly detection
- Protocol fingerprinting
- Real-time target intelligence
- Defense detection and evasion
"""

from .traffic_analysis import (
    TrafficType, AnomalyType, PacketInfo, FlowInfo, Anomaly,
    PacketAnalyzer, FlowTracker, AnomalyDetector,
    ProtocolFingerprinter, TrafficIntelligence
)

from .realtime_intelligence import (
    DefenseType, TargetState, TargetProfile, IntelligenceReport,
    ResponseTimeAnalyzer, DefenseDetector, EffectivenessScorer,
    RateOptimizer, RealTimeIntelligence
)

__all__ = [
    # Traffic Analysis
    'TrafficType', 'AnomalyType', 'PacketInfo', 'FlowInfo', 'Anomaly',
    'PacketAnalyzer', 'FlowTracker', 'AnomalyDetector',
    'ProtocolFingerprinter', 'TrafficIntelligence',
    # Real-time Intelligence
    'DefenseType', 'TargetState', 'TargetProfile', 'IntelligenceReport',
    'ResponseTimeAnalyzer', 'DefenseDetector', 'EffectivenessScorer',
    'RateOptimizer', 'RealTimeIntelligence',
]
