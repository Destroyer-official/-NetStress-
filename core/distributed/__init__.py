"""
Distributed Testing Module

Provides multi-machine coordination for distributed stress testing:
- Controller/Agent architecture
- Secure communication
- Synchronized attacks
- Centralized monitoring

WARNING: For authorized security testing only.
"""

from .controller import DistributedController, ControllerConfig
from .agent import DistributedAgent, AgentConfig
from .protocol import ControlMessage, MessageType, AgentStatus
from .coordinator import AttackCoordinator, CoordinatedAttack

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
]
