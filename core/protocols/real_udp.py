"""
Real UDP packet generator.

This module generates actual UDP packets using real socket.sendto() calls.
No simulations - every packet is genuinely sent over the network.
"""

import socket
import time
import logging
import random
import struct
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UDPPacketStats:
    """Statistics for UDP packet generation"""
    packets_sent: int = 0
    bytes_sent: int = 0
    packets_failed: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def packets_per_second(self) -> float:
        if self.duration > 0:
            return self.packets_sent / self.duration
        return 0.0
    
    @property
    def bytes_per_second(self) -> float:
        if self.duration > 0:
            return self.bytes_sent / self.duration
        return 0.0


class RealUDPGenerator:
    """
    Real UDP packet generator using actual socket operations.
    
    This class generates genuine UDP packets with configurable payloads
    and sends them using real socket.sendto() calls. No simulations.
    """
    
    def __init__(self, target_host: str, target_port: int, source_port: Optional[int] = None):
        """
        Initialize UDP generator.
        
        Args:
            target_host: Target IP address or hostname
            target_port: Target UDP port
            source_port: Source port (random if None)
        """
        self.target_host = target_host
        self.target_port = target_port
        self.source_port = source_port or random.randint(1024, 65535)
        self.socket = None
        self.stats = UDPPacketStats()
        
    def __enter__(self):
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def open(self) -> None:
        """Open UDP socket with optimizations"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Bind to specific source port if requested
            if self.source_port:
                self.socket.bind(('', self.source_port))
            
            # Apply socket optimizations
            self._apply_socket_optimizations()
            
            logger.info(f"UDP generator opened: {self.target_host}:{self.target_port}")
            
        except Exception as e:
            logger.error(f"Failed to open UDP socket: {e}")
            raise
            
    def close(self) -> None:
        """Close UDP socket"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("UDP generator closed")
            except Exception as e:
                logger.warning(f"Error closing UDP socket: {e}")
            finally:
                self.socket = None
                
    def _apply_socket_optimizations(self) -> None:
        """Apply real socket optimizations"""
        if not self.socket:
            return
            
        try:
            # Set send buffer size
            desired_sndbuf = 1024 * 1024  # 1MB
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, desired_sndbuf)
            actual_sndbuf = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            logger.debug(f"SO_SNDBUF: requested {desired_sndbuf}, got {actual_sndbuf}")
            
            # Set socket to non-blocking for better performance
            self.socket.setblocking(False)
            
        except Exception as e:
            logger.warning(f"Failed to apply socket optimizations: {e}")
            
    def generate_payload(self, size: int, pattern: str = 'random') -> bytes:
        """
        Generate UDP payload data.
        
        Args:
            size: Payload size in bytes
            pattern: Payload pattern ('random', 'zeros', 'ones', 'sequence')
            
        Returns:
            Payload bytes
        """
        if size <= 0:
            return b''
            
        if pattern == 'random':
            return bytes(random.getrandbits(8) for _ in range(size))
        elif pattern == 'zeros':
            return b'\x00' * size
        elif pattern == 'ones':
            return b'\xff' * size
        elif pattern == 'sequence':
            return bytes(i % 256 for i in range(size))
        else:
            # Default to random
            return bytes(random.getrandbits(8) for _ in range(size))
            
    def send_packet(self, payload: bytes) -> bool:
        """
        Send a single UDP packet.
        
        Args:
            payload: Packet payload data
            
        Returns:
            True if packet sent successfully, False otherwise
        """
        if not self.socket:
            logger.error("Socket not opened")
            return False
            
        try:
            bytes_sent = self.socket.sendto(payload, (self.target_host, self.target_port))
            
            # Update statistics
            self.stats.packets_sent += 1
            self.stats.bytes_sent += bytes_sent
            
            logger.debug(f"Sent UDP packet: {bytes_sent} bytes to {self.target_host}:{self.target_port}")
            return True
            
        except socket.error as e:
            if e.errno == 11:  # EAGAIN/EWOULDBLOCK
                logger.debug("Socket buffer full, packet dropped")
            elif e.errno == 10055:  # WSAENOBUFS on Windows
                logger.debug("Windows socket buffer exhausted")
            else:
                logger.warning(f"UDP send failed: {e}")
                
            self.stats.packets_failed += 1
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending UDP packet: {e}")
            self.stats.packets_failed += 1
            return False
            
    def send_burst(self, packet_count: int, payload_size: int, 
                   pattern: str = 'random', delay_ms: float = 0) -> UDPPacketStats:
        """
        Send a burst of UDP packets.
        
        Args:
            packet_count: Number of packets to send
            payload_size: Size of each packet payload
            pattern: Payload pattern
            delay_ms: Delay between packets in milliseconds
            
        Returns:
            Statistics for the burst
        """
        if not self.socket:
            raise RuntimeError("Socket not opened")
            
        # Reset statistics
        burst_stats = UDPPacketStats()
        burst_stats.start_time = time.perf_counter()
        
        logger.info(f"Starting UDP burst: {packet_count} packets, {payload_size} bytes each")
        
        for i in range(packet_count):
            payload = self.generate_payload(payload_size, pattern)
            
            if self.send_packet(payload):
                burst_stats.packets_sent += 1
                burst_stats.bytes_sent += len(payload)
            else:
                burst_stats.packets_failed += 1
                
            # Apply delay if specified
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
                
        burst_stats.end_time = time.perf_counter()
        
        logger.info(f"UDP burst complete: {burst_stats.packets_sent}/{packet_count} sent, "
                   f"{burst_stats.packets_per_second:.1f} PPS, "
                   f"{burst_stats.bytes_per_second / 1024 / 1024:.2f} MB/s")
        
        return burst_stats
        
    def send_flood(self, duration_seconds: float, payload_size: int, 
                   pattern: str = 'random', max_rate_pps: Optional[int] = None) -> UDPPacketStats:
        """
        Send UDP flood for specified duration.
        
        Args:
            duration_seconds: How long to flood
            payload_size: Size of each packet payload  
            pattern: Payload pattern
            max_rate_pps: Maximum rate in packets per second (None for unlimited)
            
        Returns:
            Statistics for the flood
        """
        if not self.socket:
            raise RuntimeError("Socket not opened")
            
        flood_stats = UDPPacketStats()
        flood_stats.start_time = time.perf_counter()
        end_time = flood_stats.start_time + duration_seconds
        
        # Calculate delay for rate limiting
        packet_delay = 1.0 / max_rate_pps if max_rate_pps else 0
        
        logger.info(f"Starting UDP flood: {duration_seconds}s duration, "
                   f"{payload_size} byte packets, "
                   f"{'unlimited' if not max_rate_pps else f'{max_rate_pps} PPS'} rate")
        
        last_packet_time = flood_stats.start_time
        
        while time.perf_counter() < end_time:
            current_time = time.perf_counter()
            
            # Rate limiting
            if packet_delay > 0:
                time_since_last = current_time - last_packet_time
                if time_since_last < packet_delay:
                    time.sleep(packet_delay - time_since_last)
                    
            payload = self.generate_payload(payload_size, pattern)
            
            if self.send_packet(payload):
                flood_stats.packets_sent += 1
                flood_stats.bytes_sent += len(payload)
            else:
                flood_stats.packets_failed += 1
                
            last_packet_time = time.perf_counter()
            
        flood_stats.end_time = time.perf_counter()
        
        logger.info(f"UDP flood complete: {flood_stats.packets_sent} packets sent, "
                   f"{flood_stats.packets_per_second:.1f} PPS, "
                   f"{flood_stats.bytes_per_second / 1024 / 1024:.2f} MB/s")
        
        return flood_stats
        
    def get_stats(self) -> UDPPacketStats:
        """Get current statistics"""
        return self.stats


def create_udp_generator(target_host: str, target_port: int, 
                        source_port: Optional[int] = None) -> RealUDPGenerator:
    """
    Factory function to create UDP generator.
    
    Args:
        target_host: Target IP address or hostname
        target_port: Target UDP port
        source_port: Source port (random if None)
        
    Returns:
        Configured UDP generator
    """
    return RealUDPGenerator(target_host, target_port, source_port)