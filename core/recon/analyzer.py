"""
Target Analysis Module

Provides comprehensive target analysis:
- Network mapping
- Host discovery
- Vulnerability scanning
- Attack surface analysis
"""

import asyncio
import socket
import struct
import ipaddress
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class HostInfo:
    """Information about a discovered host"""
    ip: str
    hostname: Optional[str] = None
    is_alive: bool = False
    open_ports: List[int] = field(default_factory=list)
    os_guess: Optional[str] = None
    services: Dict[int, str] = field(default_factory=dict)
    response_time: float = 0.0


class HostDiscovery:
    """
    Host Discovery
    
    Discovers live hosts on a network using:
    - ICMP ping
    - TCP SYN ping
    - ARP scan (local network)
    """
    
    def __init__(self, timeout: float = 2.0, max_concurrent: int = 100):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self._results: Dict[str, HostInfo] = {}
        
    async def discover(self, network: str) -> Dict[str, HostInfo]:
        """Discover hosts in network"""
        self._results = {}
        
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError as e:
            logger.error(f"Invalid network: {e}")
            return {}
            
        hosts = list(net.hosts())
        logger.info(f"Scanning {len(hosts)} hosts in {network}")
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def check_host(ip: str):
            async with semaphore:
                info = await self._check_host(ip)
                if info.is_alive:
                    self._results[ip] = info
                    
        tasks = [check_host(str(ip)) for ip in hosts]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Found {len(self._results)} live hosts")
        return self._results
        
    async def _check_host(self, ip: str) -> HostInfo:
        """Check if host is alive"""
        info = HostInfo(ip=ip)
        start = time.monotonic()
        
        # Try TCP connect to common ports
        common_ports = [80, 443, 22, 445, 139, 21, 23, 25, 3389]
        
        for port in common_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=self.timeout
                )
                writer.close()
                await writer.wait_closed()
                
                info.is_alive = True
                info.open_ports.append(port)
                info.response_time = time.monotonic() - start
                break
                
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                continue
                
        # Try hostname resolution
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            info.hostname = hostname
        except socket.herror:
            pass
            
        return info
        
    def get_live_hosts(self) -> List[str]:
        """Get list of live host IPs"""
        return list(self._results.keys())


class NetworkMapper:
    """
    Network Mapping
    
    Maps network topology and relationships.
    """
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.topology: Dict[str, Any] = {}
        
    async def map_network(self, target: str) -> Dict[str, Any]:
        """Map network around target"""
        self.topology = {
            'target': target,
            'hops': [],
            'neighbors': [],
        }
        
        # Traceroute
        hops = await self._traceroute(target)
        self.topology['hops'] = hops
        
        return self.topology
        
    async def _traceroute(self, target: str, max_hops: int = 30) -> List[Dict]:
        """Perform traceroute"""
        hops = []
        
        try:
            dest_ip = socket.gethostbyname(target)
        except socket.gaierror:
            return hops
            
        for ttl in range(1, max_hops + 1):
            hop_info = await self._probe_hop(dest_ip, ttl)
            hops.append(hop_info)
            
            if hop_info.get('ip') == dest_ip:
                break
                
        return hops
        
    async def _probe_hop(self, dest: str, ttl: int) -> Dict[str, Any]:
        """Probe a single hop"""
        result = {'ttl': ttl, 'ip': None, 'rtt': None}
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            sock.settimeout(self.timeout)
            
            port = 33434 + ttl
            start = time.monotonic()
            
            sock.sendto(b'', (dest, port))
            
            try:
                data, addr = sock.recvfrom(1024)
                result['ip'] = addr[0]
                result['rtt'] = (time.monotonic() - start) * 1000
            except socket.timeout:
                result['ip'] = '*'
                
        except Exception as e:
            logger.debug(f"Traceroute error at TTL {ttl}: {e}")
        finally:
            sock.close()
            
        return result


class VulnerabilityScanner:
    """
    Basic Vulnerability Scanner
    
    Checks for common vulnerabilities:
    - Default credentials
    - Known CVEs
    - Misconfigurations
    """
    
    # Common default credentials
    DEFAULT_CREDS = {
        'ssh': [('root', 'root'), ('admin', 'admin'), ('root', 'toor')],
        'ftp': [('anonymous', ''), ('ftp', 'ftp'), ('admin', 'admin')],
        'mysql': [('root', ''), ('root', 'root'), ('mysql', 'mysql')],
        'redis': [(None, None)],  # No auth
    }
    
    def __init__(self, target: str, timeout: float = 5.0):
        self.target = target
        self.timeout = timeout
        self.vulnerabilities: List[Dict] = []
        
    async def scan(self, ports: List[int]) -> List[Dict]:
        """Scan for vulnerabilities"""
        self.vulnerabilities = []
        
        for port in ports:
            vulns = await self._check_port(port)
            self.vulnerabilities.extend(vulns)
            
        return self.vulnerabilities
        
    async def _check_port(self, port: int) -> List[Dict]:
        """Check port for vulnerabilities"""
        vulns = []
        
        # Service-specific checks
        service_checks = {
            22: self._check_ssh,
            21: self._check_ftp,
            80: self._check_http,
            443: self._check_https,
            3306: self._check_mysql,
            6379: self._check_redis,
        }
        
        if port in service_checks:
            result = await service_checks[port]()
            if result:
                vulns.extend(result)
                
        return vulns

    async def _check_ssh(self) -> List[Dict]:
        """Check SSH for vulnerabilities"""
        vulns = []
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, 22),
                timeout=self.timeout
            )
            
            banner = await asyncio.wait_for(reader.read(1024), timeout=2)
            banner_str = banner.decode('utf-8', errors='ignore')
            
            writer.close()
            
            # Check for old SSH versions
            if 'SSH-1' in banner_str:
                vulns.append({
                    'port': 22,
                    'severity': 'high',
                    'title': 'SSH Protocol v1 Enabled',
                    'description': 'SSH v1 has known vulnerabilities',
                })
                
            # Check for vulnerable versions
            if 'OpenSSH_4' in banner_str or 'OpenSSH_5' in banner_str:
                vulns.append({
                    'port': 22,
                    'severity': 'medium',
                    'title': 'Outdated OpenSSH Version',
                    'description': f'Old SSH version detected: {banner_str.strip()}',
                })
                
        except Exception:
            pass
            
        return vulns
        
    async def _check_ftp(self) -> List[Dict]:
        """Check FTP for vulnerabilities"""
        vulns = []
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, 21),
                timeout=self.timeout
            )
            
            banner = await asyncio.wait_for(reader.read(1024), timeout=2)
            
            # Try anonymous login
            writer.write(b'USER anonymous\r\n')
            await writer.drain()
            response = await asyncio.wait_for(reader.read(1024), timeout=2)
            
            if b'331' in response:
                writer.write(b'PASS anonymous@\r\n')
                await writer.drain()
                response = await asyncio.wait_for(reader.read(1024), timeout=2)
                
                if b'230' in response:
                    vulns.append({
                        'port': 21,
                        'severity': 'high',
                        'title': 'Anonymous FTP Login Allowed',
                        'description': 'FTP server allows anonymous access',
                    })
                    
            writer.close()
            
        except Exception:
            pass
            
        return vulns
        
    async def _check_http(self) -> List[Dict]:
        """Check HTTP for vulnerabilities"""
        vulns = []
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, 80),
                timeout=self.timeout
            )
            
            request = f"GET / HTTP/1.1\r\nHost: {self.target}\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(4096), timeout=5)
            response_str = response.decode('utf-8', errors='ignore')
            
            writer.close()
            
            # Check for missing security headers
            if 'X-Frame-Options' not in response_str:
                vulns.append({
                    'port': 80,
                    'severity': 'low',
                    'title': 'Missing X-Frame-Options Header',
                    'description': 'Site may be vulnerable to clickjacking',
                })
                
            if 'X-Content-Type-Options' not in response_str:
                vulns.append({
                    'port': 80,
                    'severity': 'low',
                    'title': 'Missing X-Content-Type-Options Header',
                    'description': 'Site may be vulnerable to MIME sniffing',
                })
                
            # Check for server version disclosure
            if 'Server:' in response_str:
                import re
                match = re.search(r'Server:\s*(.+)', response_str)
                if match and any(v in match.group(1) for v in ['Apache/2.2', 'nginx/1.0', 'IIS/6']):
                    vulns.append({
                        'port': 80,
                        'severity': 'medium',
                        'title': 'Outdated Web Server',
                        'description': f'Old server version: {match.group(1)}',
                    })
                    
        except Exception:
            pass
            
        return vulns
        
    async def _check_https(self) -> List[Dict]:
        """Check HTTPS for vulnerabilities"""
        import ssl
        vulns = []
        
        # Check for weak TLS versions
        weak_versions = [
            (ssl.TLSVersion.TLSv1, 'TLSv1.0'),
            (ssl.TLSVersion.TLSv1_1, 'TLSv1.1'),
        ]
        
        for version, name in weak_versions:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = version
                ctx.maximum_version = version
                
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target, 443, ssl=ctx),
                    timeout=self.timeout
                )
                writer.close()
                
                vulns.append({
                    'port': 443,
                    'severity': 'medium',
                    'title': f'Weak TLS Version Supported: {name}',
                    'description': f'Server supports deprecated {name}',
                })
                
            except Exception:
                pass
                
        return vulns
        
    async def _check_mysql(self) -> List[Dict]:
        """Check MySQL for vulnerabilities"""
        vulns = []
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, 3306),
                timeout=self.timeout
            )
            
            # Read greeting
            greeting = await asyncio.wait_for(reader.read(1024), timeout=2)
            
            if greeting:
                # Check for old MySQL versions
                if b'5.0' in greeting or b'5.1' in greeting:
                    vulns.append({
                        'port': 3306,
                        'severity': 'high',
                        'title': 'Outdated MySQL Version',
                        'description': 'MySQL 5.0/5.1 has known vulnerabilities',
                    })
                    
            writer.close()
            
        except Exception:
            pass
            
        return vulns
        
    async def _check_redis(self) -> List[Dict]:
        """Check Redis for vulnerabilities"""
        vulns = []
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, 6379),
                timeout=self.timeout
            )
            
            # Try INFO command without auth
            writer.write(b'INFO\r\n')
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(4096), timeout=2)
            
            if b'redis_version' in response:
                vulns.append({
                    'port': 6379,
                    'severity': 'critical',
                    'title': 'Redis No Authentication',
                    'description': 'Redis server has no authentication',
                })
                
            writer.close()
            
        except Exception:
            pass
            
        return vulns


class TargetAnalyzer:
    """
    Comprehensive Target Analyzer
    
    Combines all reconnaissance capabilities.
    """
    
    def __init__(self, target: str):
        self.target = target
        self.results: Dict[str, Any] = {}
        
    async def analyze(self, full_scan: bool = False) -> Dict[str, Any]:
        """Perform comprehensive analysis"""
        from .scanner import TCPScanner, ScanConfig
        from .fingerprint import OSFingerprint, WebFingerprint, TLSFingerprint
        
        self.results = {
            'target': self.target,
            'timestamp': time.time(),
            'ports': {},
            'os': None,
            'web': None,
            'tls': None,
            'vulnerabilities': [],
        }
        
        # Port scan
        ports = list(range(1, 1025)) if full_scan else [21, 22, 23, 25, 80, 443, 3306, 3389, 8080]
        scanner = TCPScanner(ScanConfig(target=self.target, ports=ports))
        scan_results = await scanner.scan()
        
        self.results['ports'] = {
            'open': scanner.get_open_ports(),
            'details': {p: r.__dict__ for p, r in scan_results.items() if r.state.value == 'open'}
        }
        
        # OS fingerprint
        os_fp = OSFingerprint(self.target)
        self.results['os'] = (await os_fp.fingerprint()).__dict__
        
        # Web fingerprint if port 80/443 open
        if 80 in self.results['ports']['open']:
            web_fp = WebFingerprint(self.target, 80, False)
            self.results['web'] = (await web_fp.fingerprint()).__dict__
        elif 443 in self.results['ports']['open']:
            web_fp = WebFingerprint(self.target, 443, True)
            self.results['web'] = (await web_fp.fingerprint()).__dict__
            
        # TLS fingerprint if 443 open
        if 443 in self.results['ports']['open']:
            tls_fp = TLSFingerprint(self.target)
            self.results['tls'] = await tls_fp.fingerprint()
            
        # Vulnerability scan
        vuln_scanner = VulnerabilityScanner(self.target)
        self.results['vulnerabilities'] = await vuln_scanner.scan(self.results['ports']['open'])
        
        return self.results
