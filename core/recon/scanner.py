"""
Port Scanner Module

Implements various port scanning techniques:
- TCP Connect scan
- SYN scan (requires raw sockets)
- UDP scan
- Service version detection
"""

import asyncio
import socket
import struct
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PortState(Enum):
    """Port state enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    OPEN_FILTERED = "open|filtered"
    UNKNOWN = "unknown"


@dataclass
class ScanResult:
    """Result of a port scan"""
    port: int
    state: PortState
    service: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None
    response_time: float = 0.0


@dataclass
class ScanConfig:
    """Configuration for port scanning"""
    target: str
    ports: List[int] = field(default_factory=lambda: list(range(1, 1025)))
    timeout: float = 2.0
    max_concurrent: int = 100
    retries: int = 1
    randomize: bool = True


# Common service ports
COMMON_PORTS = {
    21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp', 53: 'dns',
    80: 'http', 110: 'pop3', 111: 'rpcbind', 135: 'msrpc',
    139: 'netbios-ssn', 143: 'imap', 443: 'https', 445: 'microsoft-ds',
    993: 'imaps', 995: 'pop3s', 1723: 'pptp', 3306: 'mysql',
    3389: 'ms-wbt-server', 5432: 'postgresql', 5900: 'vnc',
    6379: 'redis', 8080: 'http-proxy', 8443: 'https-alt',
    27017: 'mongodb', 11211: 'memcached',
}


class PortScanner(ABC):
    """Base class for port scanners"""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.results: Dict[int, ScanResult] = {}
        self._running = False
        
    @abstractmethod
    async def scan_port(self, port: int) -> ScanResult:
        """Scan a single port"""
        pass
    
    async def scan(self) -> Dict[int, ScanResult]:
        """Scan all configured ports"""
        self._running = True
        self.results = {}
        
        ports = self.config.ports.copy()
        if self.config.randomize:
            random.shuffle(ports)
            
        logger.info(f"Scanning {self.config.target} ({len(ports)} ports)")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def scan_with_semaphore(port: int):
            async with semaphore:
                if not self._running:
                    return
                result = await self.scan_port(port)
                self.results[port] = result
                
        tasks = [scan_with_semaphore(port) for port in ports]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self._running = False
        return self.results
    
    async def stop(self):
        """Stop scanning"""
        self._running = False
        
    def get_open_ports(self) -> List[int]:
        """Get list of open ports"""
        return [port for port, result in self.results.items() 
                if result.state == PortState.OPEN]
                
    def get_summary(self) -> Dict[str, Any]:
        """Get scan summary"""
        states = {}
        for result in self.results.values():
            state = result.state.value
            states[state] = states.get(state, 0) + 1
            
        return {
            'target': self.config.target,
            'ports_scanned': len(self.results),
            'states': states,
            'open_ports': self.get_open_ports(),
        }


class TCPScanner(PortScanner):
    """TCP Connect Scanner - Full TCP handshake"""
    
    async def scan_port(self, port: int) -> ScanResult:
        """Scan port using TCP connect"""
        start_time = time.monotonic()
        
        for attempt in range(self.config.retries + 1):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.config.target, port),
                    timeout=self.config.timeout
                )
                
                response_time = time.monotonic() - start_time
                
                # Try to grab banner
                banner = None
                try:
                    writer.write(b'\r\n')
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if data:
                        banner = data.decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
                    
                writer.close()
                await writer.wait_closed()
                
                return ScanResult(
                    port=port,
                    state=PortState.OPEN,
                    service=COMMON_PORTS.get(port),
                    banner=banner,
                    response_time=response_time
                )
                
            except asyncio.TimeoutError:
                continue
            except ConnectionRefusedError:
                return ScanResult(port=port, state=PortState.CLOSED)
            except Exception:
                continue
                
        return ScanResult(port=port, state=PortState.FILTERED)


class ConnectScanner(TCPScanner):
    """Alias for TCP Connect Scanner"""
    pass


class UDPScanner(PortScanner):
    """UDP Scanner"""
    
    async def scan_port(self, port: int) -> ScanResult:
        """Scan port using UDP"""
        start_time = time.monotonic()
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.settimeout(self.config.timeout)
            
            # Send probe
            probe = self._get_probe(port)
            sock.sendto(probe, (self.config.target, port))
            
            # Wait for response
            try:
                loop = asyncio.get_event_loop()
                data = await asyncio.wait_for(
                    loop.sock_recv(sock, 1024),
                    timeout=self.config.timeout
                )
                
                response_time = time.monotonic() - start_time
                
                return ScanResult(
                    port=port,
                    state=PortState.OPEN,
                    service=COMMON_PORTS.get(port),
                    banner=data.decode('utf-8', errors='ignore')[:100] if data else None,
                    response_time=response_time
                )
                
            except asyncio.TimeoutError:
                # No response - could be open or filtered
                return ScanResult(port=port, state=PortState.OPEN_FILTERED)
                
        except Exception:
            return ScanResult(port=port, state=PortState.UNKNOWN)
        finally:
            try:
                sock.close()
            except Exception:
                pass
                
    def _get_probe(self, port: int) -> bytes:
        """Get appropriate probe for port"""
        probes = {
            53: b'\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00',  # DNS
            123: b'\x1b' + b'\x00' * 47,  # NTP
            161: b'\x30\x26\x02\x01\x01\x04\x06public',  # SNMP
            1900: b'M-SEARCH * HTTP/1.1\r\nHost:239.255.255.250:1900\r\n\r\n',  # SSDP
        }
        return probes.get(port, b'\x00')


class SYNScanner(PortScanner):
    """
    SYN Scanner - Half-open scanning
    
    Requires raw sockets (root/admin privileges).
    Falls back to TCP connect if raw sockets unavailable.
    """
    
    def __init__(self, config: ScanConfig):
        super().__init__(config)
        self._raw_available = self._check_raw_sockets()
        
    def _check_raw_sockets(self) -> bool:
        """Check if raw sockets are available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.close()
            return True
        except (PermissionError, OSError):
            return False
            
    async def scan_port(self, port: int) -> ScanResult:
        """Scan port using SYN packets"""
        if not self._raw_available:
            # Fall back to TCP connect
            scanner = TCPScanner(ScanConfig(
                target=self.config.target,
                ports=[port],
                timeout=self.config.timeout
            ))
            return await scanner.scan_port(port)
            
        # Raw socket SYN scan implementation
        start_time = time.monotonic()
        
        try:
            # Create raw socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            sock.setblocking(False)
            
            # Build SYN packet
            src_port = random.randint(1024, 65535)
            packet = self._build_syn_packet(src_port, port)
            
            # Send packet
            sock.sendto(packet, (self.config.target, 0))
            
            # Wait for response
            loop = asyncio.get_event_loop()
            try:
                response = await asyncio.wait_for(
                    loop.sock_recv(sock, 1024),
                    timeout=self.config.timeout
                )
                
                # Parse response
                if len(response) >= 40:
                    tcp_header = response[20:40]
                    flags = tcp_header[13]
                    
                    if flags & 0x12 == 0x12:  # SYN-ACK
                        return ScanResult(
                            port=port,
                            state=PortState.OPEN,
                            service=COMMON_PORTS.get(port),
                            response_time=time.monotonic() - start_time
                        )
                    elif flags & 0x04:  # RST
                        return ScanResult(port=port, state=PortState.CLOSED)
                        
            except asyncio.TimeoutError:
                return ScanResult(port=port, state=PortState.FILTERED)
                
        except Exception as e:
            logger.debug(f"SYN scan error on port {port}: {e}")
            return ScanResult(port=port, state=PortState.UNKNOWN)
        finally:
            try:
                sock.close()
            except Exception:
                pass
                
        return ScanResult(port=port, state=PortState.UNKNOWN)
        
    def _build_syn_packet(self, src_port: int, dst_port: int) -> bytes:
        """Build a TCP SYN packet"""
        # IP header
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            0x45,  # Version + IHL
            0,     # TOS
            40,    # Total length
            random.randint(1, 65535),  # ID
            0,     # Flags + Fragment offset
            64,    # TTL
            socket.IPPROTO_TCP,  # Protocol
            0,     # Checksum (will be filled by kernel)
            socket.inet_aton('0.0.0.0'),  # Source (will be filled)
            socket.inet_aton(self.config.target)  # Destination
        )
        
        # TCP header
        seq = random.randint(0, 2**32 - 1)
        tcp_header = struct.pack(
            '!HHLLBBHHH',
            src_port,  # Source port
            dst_port,  # Destination port
            seq,       # Sequence number
            0,         # Acknowledgment number
            0x50,      # Data offset (5 words)
            0x02,      # Flags (SYN)
            65535,     # Window size
            0,         # Checksum (calculated below)
            0          # Urgent pointer
        )
        
        return ip_header + tcp_header


class ServiceDetector:
    """
    Service Version Detection
    
    Probes open ports to identify service versions.
    """
    
    # Service probes
    PROBES = {
        'http': b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n',
        'https': b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n',
        'ftp': b'',  # FTP sends banner on connect
        'ssh': b'',  # SSH sends banner on connect
        'smtp': b'EHLO test\r\n',
        'pop3': b'',  # POP3 sends banner on connect
        'imap': b'',  # IMAP sends banner on connect
        'mysql': b'',  # MySQL sends banner on connect
        'redis': b'INFO\r\n',
        'mongodb': b'\x3a\x00\x00\x00',  # MongoDB wire protocol
    }
    
    # Version patterns
    VERSION_PATTERNS = {
        'ssh': r'SSH-[\d.]+-(\S+)',
        'http': r'Server:\s*(.+)',
        'ftp': r'220[- ](.+)',
        'smtp': r'220[- ](.+)',
        'mysql': r'(\d+\.\d+\.\d+)',
    }
    
    def __init__(self, target: str, timeout: float = 5.0):
        self.target = target
        self.timeout = timeout
        
    async def detect(self, port: int, service_hint: Optional[str] = None) -> Dict[str, Any]:
        """Detect service on port"""
        result = {
            'port': port,
            'service': service_hint or COMMON_PORTS.get(port, 'unknown'),
            'version': None,
            'banner': None,
            'extra_info': {}
        }
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, port),
                timeout=self.timeout
            )
            
            # Get probe for service
            probe = self.PROBES.get(result['service'], b'\r\n')
            
            # Send probe
            if probe:
                writer.write(probe)
                await writer.drain()
                
            # Read response
            try:
                data = await asyncio.wait_for(reader.read(4096), timeout=2.0)
                if data:
                    result['banner'] = data.decode('utf-8', errors='ignore')[:500]
                    
                    # Try to extract version
                    import re
                    pattern = self.VERSION_PATTERNS.get(result['service'])
                    if pattern:
                        match = re.search(pattern, result['banner'], re.IGNORECASE)
                        if match:
                            result['version'] = match.group(1).strip()
                            
            except asyncio.TimeoutError:
                pass
                
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
        
    async def detect_all(self, ports: List[int]) -> List[Dict[str, Any]]:
        """Detect services on multiple ports"""
        tasks = [self.detect(port) for port in ports]
        return await asyncio.gather(*tasks, return_exceptions=True)
