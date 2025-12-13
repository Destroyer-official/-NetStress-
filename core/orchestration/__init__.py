"""
Attack Orchestration Module

Advanced multi-vector attack orchestration with:
- Phase-based attack progression
- AI-driven adaptive optimization
- Real-time effectiveness monitoring
- Dynamic resource allocation
"""

from .attack_orchestrator import (
    AttackPhase,
    VectorType,
    AttackVector,
    OrchestratorConfig,
    OrchestratorStats,
    VectorEngine,
    PhaseController,
    AdaptiveController,
    AttackOrchestrator,
    MultiTargetOrchestrator,
    create_orchestrator
)

__all__ = [
    'AttackPhase',
    'VectorType',
    'AttackVector',
    'OrchestratorConfig',
    'OrchestratorStats',
    'VectorEngine',
    'PhaseController',
    'AdaptiveController',
    'AttackOrchestrator',
    'MultiTargetOrchestrator',
    'create_orchestrator'
]
