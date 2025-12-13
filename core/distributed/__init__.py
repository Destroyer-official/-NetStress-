"""
Distributed Testing Module

Provides multi-machine coordination for distributed stress testing:
- Controller/Agent architecture
- Secure communication
- Synchronized attacks (NTP-based time sync)
- Centralized monitoring
- Real-time statistics aggregation
- Load redistribution on agent failure

WARNING: For authorized security testing only.
"""

from .controller import DistributedController, ControllerConfig
from .agent import DistributedAgent, AgentConfig
from .protocol import ControlMessage, MessageType, AgentStatus
from .coordinator import AttackCoordinator, CoordinatedAttack
from .time_sync import (
    ControllerTimeSync, AgentTimeSync, NTPClient, 
    TimeSyncResult, NTPPacket
)
from .stats_aggregator import (
    StatsAggregator, AggregatedStats, AgentStats
)
from .load_balancer import (
    LoadBalancer, AgentLoadInfo, AgentHealth, RedistributionEvent
)

__all__ = [
    'DistributedController',
    'ControllerConfig',
    'DistributedAgent', 
    'AgentConfig',
    'ControlMessage',
    'MessageType',
    'AgentStatus',
    'AttackCoordinator',
    'CoordinatedAttack',
    'ControllerTimeSync',
    'AgentTimeSync',
    'NTPClient',
    'TimeSyncResult',
    'NTPPacket',
    'StatsAggregator',
    'AggregatedStats',
    'AgentStats',
    'LoadBalancer',
    'AgentLoadInfo',
    'AgentHealth',
    'RedistributionEvent',
]
