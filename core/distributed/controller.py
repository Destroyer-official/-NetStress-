"""
Distributed Controller

Central controller for coordinating distributed stress tests.
Manages multiple agents and synchronizes attacks.
"""

import asyncio
import socket
import ssl
import time
import uuid
import platform
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import logging

from .protocol import (
    ControlMessage, MessageType, AgentStatus, AgentInfo,
    AttackConfig, MessageBuilder
)

logger = logging.getLogger(__name__)


@dataclass
class ControllerConfig:
    """Configuration for the distributed controller"""
    bind_address: str = "0.0.0.0"
    bind_port: int = 9999
    secret_key: bytes = b""  # Shared secret for authentication
    heartbeat_interval: float = 5.0
    heartbeat_timeout: float = 15.0
    max_agents: int = 100
    use_ssl: bool = False
    ssl_cert: str = ""
    ssl_key: str = ""


class DistributedController:
    """
    Central controller for distributed stress testing.
    
    Features:
    - Agent registration and management
    - Synchronized attack coordination
    - Real-time statistics aggregation
    - Fault tolerance with agent failover
    """
    
    def __init__(self, config: Optional[ControllerConfig] = None):
        self.config = config or ControllerConfig()
        self.controller_id = f"controller-{uuid.uuid4().hex[:8]}"
        self.msg_builder = MessageBuilder(self.controller_id)
        
        # Agent management
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_connections: Dict[str, asyncio.StreamWriter] = {}
        self._agent_readers: Dict[str, asyncio.StreamReader] = {}
        
        # Attack state
        self.current_attack: Optional[AttackConfig] = None
        self.attack_active = False
        self.attack_start_time = 0.0
        
        # Statistics
        self.aggregated_stats: Dict[str, Any] = defaultdict(int)
        self._stats_callbacks: List[Callable] = []
        
        # Server state
        self._server: Optional[asyncio.Server] = None
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the controller server"""
        logger.info(f"Starting controller on {self.config.bind_address}:{self.config.bind_port}")
        
        # Create SSL context if enabled
        ssl_context = None
        if self.config.use_ssl and self.config.ssl_cert and self.config.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.config.ssl_cert, self.config.ssl_key)
        
        self._server = await asyncio.start_server(
            self._handle_connection,
            self.config.bind_address,
            self.config.bind_port,
            ssl=ssl_context
        )
        
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        
        logger.info(f"Controller started with ID: {self.controller_id}")
        
    async def stop(self):
        """Stop the controller server"""
        logger.info("Stopping controller...")
        self._running = False
        
        # Send shutdown to all agents
        await self.broadcast(self.msg_builder.stop_attack())
        
        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all agent connections
        for writer in self.agent_connections.values():
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        
        # Stop server
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            
        logger.info("Controller stopped")
        
    async def _handle_connection(self, reader: asyncio.StreamReader, 
                                  writer: asyncio.StreamWriter):
        """Handle incoming agent connection"""
        peer = writer.get_extra_info('peername')
        logger.info(f"New connection from {peer}")
        
        agent_id = None
        
        try:
            while self._running:
                # Read message length
                length_data = await reader.read(4)
                if not length_data:
                    break
                    
                import struct
                length = struct.unpack('>I', length_data)[0]
                
                # Read message body
                data = await reader.read(length)
                if not data:
                    break
                
                # Parse message
                try:
                    msg = ControlMessage.from_bytes(
                        length_data + data,
                        self.config.secret_key if self.config.secret_key else None
                    )
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue
                
                # Handle message
                response = await self._handle_message(msg, reader, writer)
                
                if response:
                    await self._send_message(writer, response)
                    
                # Track agent ID for cleanup
                if msg.msg_type == MessageType.REGISTER:
                    agent_id = msg.sender_id
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            # Cleanup
            if agent_id and agent_id in self.agents:
                self.agents[agent_id].status = AgentStatus.OFFLINE
                if agent_id in self.agent_connections:
                    del self.agent_connections[agent_id]
                if agent_id in self._agent_readers:
                    del self._agent_readers[agent_id]
                    
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
                
            logger.info(f"Connection closed: {peer}")
            
    async def _handle_message(self, msg: ControlMessage, 
                              reader: asyncio.StreamReader,
                              writer: asyncio.StreamWriter) -> Optional[ControlMessage]:
        """Handle incoming control message"""
        
        if msg.msg_type == MessageType.REGISTER:
            return await self._handle_register(msg, reader, writer)
            
        elif msg.msg_type == MessageType.HEARTBEAT:
            return await self._handle_heartbeat(msg)
            
        elif msg.msg_type == MessageType.STATUS_REPORT:
            return await self._handle_status_report(msg)
            
        elif msg.msg_type == MessageType.STATS_REPORT:
            return await self._handle_stats_report(msg)
            
        elif msg.msg_type == MessageType.READY_ACK:
            return await self._handle_ready_ack(msg)
            
        elif msg.msg_type == MessageType.ERROR_REPORT:
            return await self._handle_error_report(msg)
            
        else:
            logger.warning(f"Unknown message type: {msg.msg_type}")
            return None
            
    async def _handle_register(self, msg: ControlMessage,
                               reader: asyncio.StreamReader,
                               writer: asyncio.StreamWriter) -> ControlMessage:
        """Handle agent registration"""
        agent_id = msg.sender_id
        payload = msg.payload
        
        peer = writer.get_extra_info('peername')
        
        # Create agent info
        agent = AgentInfo(
            agent_id=agent_id,
            hostname=payload.get('hostname', 'unknown'),
            ip_address=peer[0] if peer else 'unknown',
            port=peer[1] if peer else 0,
            status=AgentStatus.IDLE,
            capabilities=payload.get('capabilities', {}),
            registered_at=time.time(),
            last_heartbeat=time.time(),
        )
        
        # Check max agents
        if len(self.agents) >= self.config.max_agents:
            logger.warning(f"Max agents reached, rejecting {agent_id}")
            return ControlMessage(
                msg_type=MessageType.REGISTER_ACK,
                sender_id=self.controller_id,
                payload={'accepted': False, 'reason': 'max_agents_reached'}
            )
        
        # Register agent
        self.agents[agent_id] = agent
        self.agent_connections[agent_id] = writer
        self._agent_readers[agent_id] = reader
        
        logger.info(f"Agent registered: {agent_id} ({agent.hostname})")
        
        return ControlMessage(
            msg_type=MessageType.REGISTER_ACK,
            sender_id=self.controller_id,
            payload={
                'accepted': True,
                'controller_id': self.controller_id,
                'heartbeat_interval': self.config.heartbeat_interval,
            }
        )
        
    async def _handle_heartbeat(self, msg: ControlMessage) -> ControlMessage:
        """Handle agent heartbeat"""
        agent_id = msg.sender_id
        
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = time.time()
            self.agents[agent_id].status = AgentStatus(msg.payload.get('status', 'idle'))
            
            if 'stats' in msg.payload:
                self.agents[agent_id].current_stats = msg.payload['stats']
                
        return ControlMessage(
            msg_type=MessageType.HEARTBEAT_ACK,
            sender_id=self.controller_id,
            payload={'server_time': time.time()}
        )
        
    async def _handle_status_report(self, msg: ControlMessage) -> None:
        """Handle status report from agent"""
        agent_id = msg.sender_id
        
        if agent_id in self.agents:
            self.agents[agent_id].status = AgentStatus(msg.payload.get('status', 'idle'))
            self.agents[agent_id].current_stats = msg.payload.get('stats', {})
            
        # Aggregate stats
        self._aggregate_stats()
        
        return None
        
    async def _handle_stats_report(self, msg: ControlMessage) -> None:
        """Handle statistics report from agent"""
        agent_id = msg.sender_id
        
        if agent_id in self.agents:
            self.agents[agent_id].current_stats = msg.payload.get('stats', {})
            
        # Aggregate stats
        self._aggregate_stats()
        
        # Notify callbacks
        for callback in self._stats_callbacks:
            try:
                callback(self.aggregated_stats)
            except Exception as e:
                logger.error(f"Stats callback error: {e}")
                
        return None
        
    async def _handle_ready_ack(self, msg: ControlMessage) -> None:
        """Handle ready acknowledgment"""
        agent_id = msg.sender_id
        
        if agent_id in self.agents and msg.payload.get('ready'):
            self.agents[agent_id].status = AgentStatus.READY
            
        return None
        
    async def _handle_error_report(self, msg: ControlMessage) -> None:
        """Handle error report from agent"""
        agent_id = msg.sender_id
        error = msg.payload.get('error', 'Unknown error')
        
        logger.error(f"Agent {agent_id} error: {error}")
        
        if agent_id in self.agents:
            self.agents[agent_id].status = AgentStatus.ERROR
            
        return None
        
    async def _send_message(self, writer: asyncio.StreamWriter, msg: ControlMessage):
        """Send message to agent"""
        data = msg.to_bytes(self.config.secret_key if self.config.secret_key else None)
        writer.write(data)
        await writer.drain()
        
    async def broadcast(self, msg: ControlMessage):
        """Broadcast message to all connected agents"""
        for agent_id, writer in list(self.agent_connections.items()):
            try:
                await self._send_message(writer, msg)
            except Exception as e:
                logger.error(f"Failed to send to {agent_id}: {e}")
                
    async def send_to_agent(self, agent_id: str, msg: ControlMessage) -> bool:
        """Send message to specific agent"""
        if agent_id not in self.agent_connections:
            return False
            
        try:
            await self._send_message(self.agent_connections[agent_id], msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send to {agent_id}: {e}")
            return False
            
    async def _heartbeat_monitor(self):
        """Monitor agent heartbeats and remove dead agents"""
        while self._running:
            await asyncio.sleep(self.config.heartbeat_interval)
            
            now = time.time()
            dead_agents = []
            
            for agent_id, agent in self.agents.items():
                if now - agent.last_heartbeat > self.config.heartbeat_timeout:
                    logger.warning(f"Agent {agent_id} heartbeat timeout")
                    dead_agents.append(agent_id)
                    
            for agent_id in dead_agents:
                self.agents[agent_id].status = AgentStatus.OFFLINE
                if agent_id in self.agent_connections:
                    try:
                        self.agent_connections[agent_id].close()
                    except Exception:
                        pass
                    del self.agent_connections[agent_id]
                    
    def _aggregate_stats(self):
        """Aggregate statistics from all agents"""
        self.aggregated_stats = defaultdict(int)
        
        for agent in self.agents.values():
            stats = agent.current_stats
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    self.aggregated_stats[key] += value
                    
        self.aggregated_stats['active_agents'] = sum(
            1 for a in self.agents.values() 
            if a.status in [AgentStatus.ATTACKING, AgentStatus.READY]
        )
        self.aggregated_stats['total_agents'] = len(self.agents)
        
    # Public API
    
    async def start_attack(self, config: AttackConfig, sync: bool = True) -> bool:
        """
        Start distributed attack across all agents.
        
        Args:
            config: Attack configuration
            sync: Wait for all agents to be ready before starting
            
        Returns:
            True if attack started successfully
        """
        if not self.agents:
            logger.error("No agents connected")
            return False
            
        self.current_attack = config
        
        # If sync start, wait for all agents ready
        if sync and config.sync_start:
            # Send ready check
            await self.broadcast(ControlMessage(
                msg_type=MessageType.READY_CHECK,
                sender_id=self.controller_id,
            ))
            
            # Wait for ready acknowledgments (with timeout)
            timeout = 10.0
            start = time.time()
            while time.time() - start < timeout:
                ready_count = sum(
                    1 for a in self.agents.values() 
                    if a.status == AgentStatus.READY
                )
                if ready_count == len(self.agents):
                    break
                await asyncio.sleep(0.1)
            else:
                logger.warning("Not all agents ready, proceeding anyway")
        
        # Set synchronized start time if needed
        if config.start_time == 0 and sync:
            config.start_time = time.time() + 2.0  # Start in 2 seconds
            
        # Send start command
        msg = self.msg_builder.start_attack(config)
        await self.broadcast(msg)
        
        self.attack_active = True
        self.attack_start_time = config.start_time or time.time()
        
        logger.info(f"Attack started: {config.target}:{config.port} ({config.protocol})")
        return True
        
    async def stop_attack(self):
        """Stop the distributed attack"""
        msg = self.msg_builder.stop_attack()
        await self.broadcast(msg)
        
        self.attack_active = False
        self.current_attack = None
        
        logger.info("Attack stopped")
        
    def get_agents(self) -> List[AgentInfo]:
        """Get list of all agents"""
        return list(self.agents.values())
        
    def get_active_agents(self) -> List[AgentInfo]:
        """Get list of active agents"""
        return [a for a in self.agents.values() 
                if a.status in [AgentStatus.ATTACKING, AgentStatus.READY, AgentStatus.IDLE]]
        
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        self._aggregate_stats()
        return dict(self.aggregated_stats)
        
    def on_stats_update(self, callback: Callable):
        """Register callback for stats updates"""
        self._stats_callbacks.append(callback)
