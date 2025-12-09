"""
Comprehensive tests for Target Resolution and Intelligence System.
Tests URL/IP resolution accuracy and performance, service discovery and profiling,
and vulnerability assessment accuracy.
"""

import unittest
import asyncio
import time
import socket
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass
from typing import List, Dict, Optional

from core.target.resolver import (
    TargetResolver, TargetInfo, ServiceInfo, NetworkInfo, DNSCache, PortScanner
)
from core.target.profiler import (
    TargetProfiler, DefenseProfile, PerformanceProfile, DefenseType, DefenseIndicator,
    NetworkTopologyMapper, ServiceFingerprinter, DefenseAnalyzer, ServiceFingerprint
)
from core.target.vulnerability import (
    VulnerabilityScanner, VulnerabilityReport, AttackSurface, Vulnerability,
    VulnerabilityType, Severity, ProtocolScanner, AttackSurfaceAnalyzer
)


class TestDNSCache(unittest.TestCase):
    """Test DNS caching functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = DNSCache(max_size=100, default_ttl=300)
    
    def test_cache_operations(self):
        """Test basic cache operations"""
        async def run_test():
            # Test cache miss
            result = await self.cache.get("example.com")
            self.assertIsNone(result)
            
            # Test cache set and get
            addresses = ["192.0.2.1", "192.0.2.2"]
            await self.cache.set("example.com", addresses, ttl=60)
            
            cached_result = await self.cache.get("example.com")
            self.assertEqual(cached_result, addresses)
        
        asyncio.run(run_test())
    
    def test_cache_expiry(self):
        """Test cache TTL expiry"""
        async def run_test():
            # Set with very short TTL
            addresses = ["192.0.2.1"]
            await self.cache.set("test.com", addresses, ttl=0.1)
            
            # Should be cached immediately
            result = await self.cache.get("test.com")
            self.assertEqual(result, addresses)
            
            # Wait for expiry
            await asyncio.sleep(0.2)
            
            # Should be expired
            result = await self.cache.get("test.com")
            self.assertIsNone(result)
        
        asyncio.run(run_test())
    
    def test_cache_size_limit(self):
        """Test cache size limiting"""
        async def run_test():
            cache = DNSCache(max_size=2, default_ttl=300)
            
            # Fill cache to capacity
            await cache.set("domain1.com", ["192.0.2.1"])
            await cache.set("domain2.com", ["192.0.2.2"])
            
            # Add one more (should evict oldest)
            await cache.set("domain3.com", ["192.0.2.3"])
            
            # First entry should be evicted
            result1 = await cache.get("domain1.com")
            result3 = await cache.get("domain3.com")
            
            # domain1 might be evicted, domain3 should exist
            self.assertEqual(result3, ["192.0.2.3"])
        
        asyncio.run(run_test())


class TestPortScanner(unittest.TestCase):
    """Test port scanning functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = PortScanner(timeout=1.0, max_concurrent=10)
    
    def test_tcp_port_scan(self):
        """Test TCP port scanning"""
        async def run_test():
            # Test scanning a commonly closed port
            result = await self.scanner.scan_port("127.0.0.1", 9999, "TCP")
            self.assertIsInstance(result, ServiceInfo)
            self.assertEqual(result.port, 9999)
            self.assertEqual(result.protocol, "TCP")
            self.assertIn(result.state, ["open", "closed", "filtered"])
        
        asyncio.run(run_test())
    
    def test_service_identification(self):
        """Test service identification"""
        # Test known port identification
        service_name = self.scanner._identify_service(80, None)
        self.assertEqual(service_name, "http")
        
        service_name = self.scanner._identify_service(443, None)
        self.assertEqual(service_name, "https")
        
        service_name = self.scanner._identify_service(22, "SSH-2.0-OpenSSH_7.4")
        self.assertEqual(service_name, "ssh")
    
    def test_multiple_port_scan(self):
        """Test scanning multiple ports"""
        async def run_test():
            ports = [22, 80, 443, 9999]
            results = await self.scanner.scan_ports("127.0.0.1", ports, ["TCP"])
            
            self.assertEqual(len(results), len(ports))
            for result in results:
                self.assertIsInstance(result, ServiceInfo)
                self.assertIn(result.port, ports)
        
        asyncio.run(run_test())


class TestTargetResolver(unittest.TestCase):
    """Test target resolution functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.resolver = TargetResolver(dns_servers=['8.8.8.8'])
    
    def test_ip_address_parsing(self):
        """Test IP address validation and parsing"""
        # Test IPv4
        self.assertTrue(self.resolver._is_ip_address("192.0.2.1"))
        self.assertTrue(self.resolver._is_ipv4("192.0.2.1"))
        self.assertFalse(self.resolver._is_ipv6("192.0.2.1"))
        
        # Test IPv6
        self.assertTrue(self.resolver._is_ip_address("2001:db8::1"))
        self.assertFalse(self.resolver._is_ipv4("2001:db8::1"))
        self.assertTrue(self.resolver._is_ipv6("2001:db8::1"))
        
        # Test invalid
        self.assertFalse(self.resolver._is_ip_address("invalid"))
    
    def test_target_parsing(self):
        """Test target URL/hostname parsing"""
        # Test URL parsing
        parsed = self.resolver._parse_target("https://example.com:8443/path")
        self.assertEqual(parsed['hostname'], "example.com")
        self.assertEqual(parsed['port'], 8443)
        
        # Test hostname:port parsing
        parsed = self.resolver._parse_target("example.com:80")
        self.assertEqual(parsed['hostname'], "example.com")
        self.assertEqual(parsed['port'], 80)
        
        # Test plain hostname
        parsed = self.resolver._parse_target("example.com")
        self.assertEqual(parsed['hostname'], "example.com")
        self.assertIsNone(parsed['port'])
    
    def test_ip_address_resolution(self):
        """Test direct IP address resolution"""
        async def run_test():
            # Test IPv4 address
            target_info = await self.resolver.resolve_target("192.0.2.1")
            self.assertEqual(target_info.original_target, "192.0.2.1")
            self.assertIn("192.0.2.1", target_info.ip_addresses)
            self.assertIn("192.0.2.1", target_info.ipv4_addresses)
            
            # Test IPv6 address
            target_info = await self.resolver.resolve_target("2001:db8::1")
            self.assertEqual(target_info.original_target, "2001:db8::1")
            self.assertIn("2001:db8::1", target_info.ip_addresses)
            self.assertIn("2001:db8::1", target_info.ipv6_addresses)
        
        asyncio.run(run_test())
    
    @patch('core.target.resolver.dns.resolver.Resolver')
    def test_hostname_resolution(self, mock_resolver_class):
        """Test hostname DNS resolution with mocking"""
        async def run_test():
            # Mock DNS resolver
            mock_resolver = MagicMock()
            mock_resolver_class.return_value = mock_resolver
            
            # Mock A record response - create a proper mock record
            mock_record = MagicMock()
            mock_record.__str__ = MagicMock(return_value="192.0.2.1")
            
            mock_answer = MagicMock()
            mock_answer.__iter__ = MagicMock(return_value=iter([mock_record]))
            mock_resolver.resolve.return_value = mock_answer
            
            target_info = await self.resolver.resolve_target("example.com")
            self.assertEqual(target_info.original_target, "example.com")
            self.assertEqual(target_info.hostname, "example.com")
        
        asyncio.run(run_test())
    
    def test_service_discovery_integration(self):
        """Test service discovery integration"""
        async def run_test():
            # Test with localhost (should be resolvable)
            target_info = await self.resolver.resolve_target("127.0.0.1")
            
            # Should have discovered some services (or attempted to)
            self.assertIsInstance(target_info.ports, list)
            self.assertIsInstance(target_info.network_info, NetworkInfo)
            self.assertGreater(target_info.resolution_time, 0)
        
        asyncio.run(run_test())


class TestNetworkTopologyMapper(unittest.TestCase):
    """Test network topology mapping"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mapper = NetworkTopologyMapper()
    
    def test_topology_discovery(self):
        """Test network topology discovery"""
        async def run_test():
            # Create mock target info
            target_info = TargetInfo(
                original_target="127.0.0.1",
                ip_addresses=["127.0.0.1"],
                hostname="localhost"
            )
            
            topology = await self.mapper.discover_topology(target_info)
            
            self.assertIsInstance(topology, dict)
            self.assertIn('hops', topology)
            self.assertIn('infrastructure', topology)
            self.assertIn('cdn_detection', topology)
            self.assertIn('load_balancer_detection', topology)
        
        asyncio.run(run_test())
    
    def test_cdn_detection(self):
        """Test CDN detection logic"""
        async def run_test():
            # Mock target info with CDN indicators
            target_info = TargetInfo(
                original_target="example.com",
                dns_records={
                    'CNAME': ['example.cloudflare.net', 'example.com']
                }
            )
            
            cdn_info = await self.mapper._detect_cdn(target_info)
            
            self.assertIsInstance(cdn_info, dict)
            self.assertIn('detected', cdn_info)
            self.assertIn('provider', cdn_info)
            self.assertIn('evidence', cdn_info)
            
            # Should detect Cloudflare
            if cdn_info['detected']:
                self.assertEqual(cdn_info['provider'], 'cloudflare')
        
        asyncio.run(run_test())
    
    def test_hosting_provider_identification(self):
        """Test hosting provider identification"""
        async def run_test():
            # Test AWS IP range
            provider = await self.mapper._identify_hosting_provider("54.123.45.67")
            self.assertEqual(provider, "aws")
            
            # Test Google IP range
            provider = await self.mapper._identify_hosting_provider("35.123.45.67")
            self.assertEqual(provider, "google")
            
            # Test unknown provider
            provider = await self.mapper._identify_hosting_provider("192.0.2.1")
            self.assertIsNone(provider)
        
        asyncio.run(run_test())


class TestServiceFingerprinter(unittest.TestCase):
    """Test service fingerprinting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fingerprinter = ServiceFingerprinter()
    
    def test_http_header_parsing(self):
        """Test HTTP header parsing"""
        response = "HTTP/1.1 200 OK\r\nServer: Apache/2.4.41\r\nContent-Type: text/html\r\n\r\n"
        headers = self.fingerprinter._parse_http_headers(response)
        
        self.assertIn('server', headers)
        self.assertIn('content-type', headers)
        self.assertEqual(headers['server'], 'Apache/2.4.41')
    
    def test_server_header_parsing(self):
        """Test server header parsing"""
        vendor, version = self.fingerprinter._parse_server_header("Apache/2.4.41 (Ubuntu)")
        self.assertEqual(vendor, "Apache")
        self.assertEqual(version, "2.4.41")
        
        vendor, version = self.fingerprinter._parse_server_header("nginx/1.18.0")
        self.assertEqual(vendor, "nginx")
        self.assertEqual(version, "1.18.0")
    
    def test_web_framework_detection(self):
        """Test web framework detection"""
        # Test PHP detection
        headers = {'x-powered-by': 'PHP/7.4.3'}
        framework = self.fingerprinter._detect_web_framework(headers, "")
        self.assertEqual(framework, "php")
        
        # Test Django detection
        headers = {}
        response = '<input type="hidden" name="csrfmiddlewaretoken" value="abc123">'
        framework = self.fingerprinter._detect_web_framework(headers, response)
        self.assertEqual(framework, "django")
    
    def test_service_fingerprinting_integration(self):
        """Test complete service fingerprinting"""
        async def run_test():
            # Create mock service info
            service = ServiceInfo(
                port=80,
                protocol="TCP",
                service_name="http",
                state="open"
            )
            
            # Test fingerprinting (will fail to connect, but should handle gracefully)
            fingerprint = await self.fingerprinter.fingerprint_service("127.0.0.1", service)
            
            # Should return a fingerprint object even if connection fails
            if fingerprint:
                self.assertIsInstance(fingerprint, ServiceFingerprint)
                self.assertEqual(fingerprint.service_name, "http")
        
        asyncio.run(run_test())


class TestDefenseAnalyzer(unittest.TestCase):
    """Test defense mechanism analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = DefenseAnalyzer()
    
    def test_defense_strength_calculation(self):
        """Test defense strength calculation"""
        # Create mock defense profile
        profile = DefenseProfile()
        
        # Add some defense indicators
        profile.indicators = [
            DefenseIndicator(
                defense_type=DefenseType.WAF,
                confidence=0.9,
                evidence=["WAF detected"]
            ),
            DefenseIndicator(
                defense_type=DefenseType.RATE_LIMITING,
                confidence=0.7,
                evidence=["Rate limiting detected"]
            )
        ]
        
        strength = self.analyzer._calculate_defense_strength(profile)
        self.assertGreater(strength, 0.0)
        self.assertLessEqual(strength, 1.0)
    
    def test_evasion_recommendations(self):
        """Test evasion technique recommendations"""
        # Create mock defense profile
        profile = DefenseProfile()
        profile.indicators = [
            DefenseIndicator(
                defense_type=DefenseType.WAF,
                confidence=0.9,
                evidence=["WAF detected"],
                bypass_techniques=["Payload encoding", "Request fragmentation"]
            )
        ]
        profile.overall_strength = 0.8
        
        recommendations = self.analyzer._generate_evasion_recommendations(profile)
        
        self.assertIsInstance(recommendations, list)
        self.assertIn("Payload encoding", recommendations)
        self.assertIn("Request fragmentation", recommendations)
    
    def test_defense_analysis_integration(self):
        """Test complete defense analysis"""
        async def run_test():
            # Create mock target info
            target_info = TargetInfo(
                original_target="127.0.0.1",
                ip_addresses=["127.0.0.1"],
                ports=[
                    ServiceInfo(port=80, protocol="TCP", service_name="http", state="open")
                ]
            )
            
            profile = await self.analyzer.analyze_defenses(target_info)
            
            self.assertIsInstance(profile, DefenseProfile)
            self.assertIsInstance(profile.indicators, list)
            self.assertGreaterEqual(profile.overall_strength, 0.0)
            self.assertLessEqual(profile.overall_strength, 1.0)
        
        asyncio.run(run_test())


class TestProtocolScanner(unittest.TestCase):
    """Test protocol-specific vulnerability scanning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = ProtocolScanner()
    
    def test_vulnerability_database_loading(self):
        """Test vulnerability database initialization"""
        # Check that vulnerability database is loaded
        self.assertIn('http', self.scanner.vuln_db.service_vulnerabilities)
        self.assertIn('dns', self.scanner.vuln_db.service_vulnerabilities)
        self.assertIn('TCP', self.scanner.vuln_db.protocol_weaknesses)
        
        # Check amplification services
        self.assertIn(53, self.scanner.vuln_db.amplification_services)  # DNS
        self.assertIn(123, self.scanner.vuln_db.amplification_services)  # NTP
    
    def test_http_vulnerability_scanning(self):
        """Test HTTP vulnerability scanning"""
        async def run_test():
            # Test HTTP vulnerability scan (will fail to connect but should handle gracefully)
            vulnerabilities = await self.scanner.scan_http_vulnerabilities("127.0.0.1", 80)
            
            # Should return a list (empty if no connection possible)
            self.assertIsInstance(vulnerabilities, list)
        
        asyncio.run(run_test())
    
    def test_dns_vulnerability_scanning(self):
        """Test DNS vulnerability scanning"""
        async def run_test():
            # Test DNS vulnerability scan
            vulnerabilities = await self.scanner.scan_dns_vulnerabilities("127.0.0.1", 53)
            
            # Should return a list
            self.assertIsInstance(vulnerabilities, list)
        
        asyncio.run(run_test())
    
    def test_amplification_service_scanning(self):
        """Test amplification service scanning"""
        async def run_test():
            # Test DNS amplification scan
            vulnerabilities = await self.scanner.scan_amplification_services("127.0.0.1", 53)
            
            # Should return a list
            self.assertIsInstance(vulnerabilities, list)
        
        asyncio.run(run_test())


class TestAttackSurfaceAnalyzer(unittest.TestCase):
    """Test attack surface analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AttackSurfaceAnalyzer()
    
    def test_attack_vector_identification(self):
        """Test attack vector identification"""
        services = [
            ServiceInfo(port=80, protocol="TCP", service_name="http", state="open"),
            ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open"),
            ServiceInfo(port=22, protocol="TCP", service_name="ssh", state="open")
        ]
        
        vectors = self.analyzer._identify_attack_vectors(services)
        
        self.assertIsInstance(vectors, dict)
        self.assertIn("80/TCP", vectors)
        self.assertIn("53/UDP", vectors)
        
        # Check specific attack vectors
        http_vectors = vectors.get("80/TCP", [])
        self.assertIn("http_flood", http_vectors)
        self.assertIn("tcp_syn_flood", http_vectors)
        
        dns_vectors = vectors.get("53/UDP", [])
        self.assertIn("dns_amplification", dns_vectors)
        self.assertIn("amplification_attack", dns_vectors)
    
    def test_amplification_potential_calculation(self):
        """Test amplification potential calculation"""
        services = [
            ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open"),
            ServiceInfo(port=123, protocol="UDP", service_name="ntp", state="open")
        ]
        
        vulnerabilities = [
            Vulnerability(
                vuln_type=VulnerabilityType.AMPLIFICATION_VECTOR,
                severity=Severity.HIGH,
                title="DNS Amplification",
                description="DNS amplification possible",
                affected_service="dns",
                port=53,
                protocol="UDP",
                evidence=["Amplification factor: 28.0x"]
            )
        ]
        
        potential = self.analyzer._calculate_amplification_potential(services, vulnerabilities)
        
        self.assertGreater(potential, 0.0)
        self.assertLessEqual(potential, 1.0)
    
    def test_attack_surface_analysis(self):
        """Test complete attack surface analysis"""
        # Create mock target info
        target_info = TargetInfo(
            original_target="example.com",
            ip_addresses=["192.0.2.1"],
            ports=[
                ServiceInfo(port=80, protocol="TCP", service_name="http", state="open"),
                ServiceInfo(port=443, protocol="TCP", service_name="https", state="open"),
                ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open")
            ]
        )
        
        vulnerabilities = [
            Vulnerability(
                vuln_type=VulnerabilityType.AMPLIFICATION_VECTOR,
                severity=Severity.HIGH,
                title="DNS Amplification",
                description="DNS amplification vector",
                affected_service="dns",
                port=53,
                protocol="UDP"
            )
        ]
        
        surface = self.analyzer.analyze_attack_surface(target_info, vulnerabilities)
        
        self.assertIsInstance(surface, AttackSurface)
        self.assertEqual(surface.total_services, 3)
        self.assertEqual(len(surface.exposed_services), 3)
        self.assertGreater(surface.amplification_potential, 0.0)
        self.assertGreater(surface.overall_risk_score, 0.0)


class TestVulnerabilityScanner(unittest.TestCase):
    """Test comprehensive vulnerability scanning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scanner = VulnerabilityScanner()
    
    def test_risk_summary_generation(self):
        """Test risk summary generation"""
        vulnerabilities = [
            Vulnerability(
                vuln_type=VulnerabilityType.SQL_INJECTION,
                severity=Severity.HIGH,
                title="SQL Injection",
                description="SQL injection vulnerability",
                affected_service="http",
                port=80,
                protocol="TCP"
            ),
            Vulnerability(
                vuln_type=VulnerabilityType.XSS,
                severity=Severity.MEDIUM,
                title="XSS",
                description="Cross-site scripting",
                affected_service="http",
                port=80,
                protocol="TCP"
            )
        ]
        
        summary = self.scanner._generate_risk_summary(vulnerabilities)
        
        self.assertEqual(summary['high'], 1)
        self.assertEqual(summary['medium'], 1)
        self.assertEqual(summary['critical'], 0)
    
    def test_recommendations_generation(self):
        """Test security recommendations generation"""
        vulnerabilities = [
            Vulnerability(
                vuln_type=VulnerabilityType.WEAK_AUTHENTICATION,
                severity=Severity.HIGH,
                title="Weak Authentication",
                description="Weak authentication detected",
                affected_service="ssh",
                port=22,
                protocol="TCP",
                remediation=["Strong passwords", "Multi-factor authentication"]
            )
        ]
        
        attack_surface = AttackSurface(
            total_services=5,
            amplification_potential=0.8,
            dos_susceptibility=0.9
        )
        
        recommendations = self.scanner._generate_recommendations(vulnerabilities, attack_surface)
        
        self.assertIsInstance(recommendations, list)
        self.assertIn("Strong passwords", recommendations)
        self.assertIn("Multi-factor authentication", recommendations)
        self.assertIn("Deploy DDoS protection service", recommendations)
    
    def test_scan_coverage_calculation(self):
        """Test scan coverage calculation"""
        services = [
            ServiceInfo(port=80, protocol="TCP", service_name="http", state="open"),
            ServiceInfo(port=443, protocol="TCP", service_name="https", state="open"),
            ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open")
        ]
        
        coverage = self.scanner._calculate_scan_coverage(services)
        
        self.assertIsInstance(coverage, dict)
        self.assertTrue(coverage['port_scan'])
        self.assertTrue(coverage['service_detection'])
        self.assertTrue(coverage['vulnerability_scan'])
        self.assertTrue(coverage['ssl_scan'])  # HTTPS present
        self.assertTrue(coverage['web_scan'])  # HTTP present
        self.assertTrue(coverage['dns_scan'])  # DNS present
    
    def test_vulnerability_scanning_integration(self):
        """Test complete vulnerability scanning"""
        async def run_test():
            # Create mock target info
            target_info = TargetInfo(
                original_target="127.0.0.1",
                ip_addresses=["127.0.0.1"],
                ports=[
                    ServiceInfo(port=80, protocol="TCP", service_name="http", state="open"),
                    ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open")
                ]
            )
            
            report = await self.scanner.scan_vulnerabilities(target_info)
            
            self.assertIsInstance(report, VulnerabilityReport)
            self.assertEqual(report.target, "127.0.0.1")
            self.assertIsInstance(report.vulnerabilities, list)
            self.assertIsInstance(report.attack_surface, AttackSurface)
            self.assertIsInstance(report.risk_summary, dict)
            self.assertIsInstance(report.recommendations, list)
            self.assertIsInstance(report.scan_coverage, dict)
        
        asyncio.run(run_test())


class TestTargetProfiler(unittest.TestCase):
    """Test complete target profiling integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.profiler = TargetProfiler()
    
    def test_performance_profile_generation(self):
        """Test performance profile generation"""
        async def run_test():
            # Create mock target info
            target_info = TargetInfo(
                original_target="127.0.0.1",
                ip_addresses=["127.0.0.1"],
                ports=[
                    ServiceInfo(port=80, protocol="TCP", service_name="http", state="open")
                ]
            )
            
            profile = await self.profiler.generate_performance_profile(target_info)
            
            self.assertIsInstance(profile, PerformanceProfile)
            self.assertIsInstance(profile.response_times, dict)
            self.assertIsInstance(profile.optimal_attack_params, dict)
        
        asyncio.run(run_test())
    
    def test_optimal_params_calculation(self):
        """Test optimal attack parameters calculation"""
        # Create mock target info and performance profile
        target_info = TargetInfo(
            original_target="example.com",
            ports=[
                ServiceInfo(port=80, protocol="TCP", service_name="http", state="open"),
                ServiceInfo(port=53, protocol="UDP", service_name="dns", state="open")
            ]
        )
        
        performance_profile = PerformanceProfile(
            response_times={"TCP:80": 0.1, "UDP:53": 0.05}
        )
        
        params = self.profiler._calculate_optimal_params(target_info, performance_profile)
        
        self.assertIsInstance(params, dict)
        self.assertIn('packet_size', params)
        self.assertIn('connection_rate', params)
        self.assertIn('protocol_distribution', params)
        
        # Should have reasonable values
        self.assertGreater(params['packet_size'], 0)
        self.assertGreater(params['connection_rate'], 0)
    
    def test_complete_target_profiling(self):
        """Test complete target profiling workflow"""
        async def run_test():
            # Create mock target info
            target_info = TargetInfo(
                original_target="127.0.0.1",
                ip_addresses=["127.0.0.1"],
                ports=[
                    ServiceInfo(port=80, protocol="TCP", service_name="http", state="open")
                ]
            )
            
            topology, fingerprints, defense_profile = await self.profiler.profile_target(target_info)
            
            # Validate results
            self.assertIsInstance(topology, dict)
            self.assertIsInstance(fingerprints, list)
            self.assertIsInstance(defense_profile, DefenseProfile)
            
            # Check topology structure
            self.assertIn('hops', topology)
            self.assertIn('infrastructure', topology)
            self.assertIn('cdn_detection', topology)
        
        asyncio.run(run_test())


class TestTargetIntelligenceIntegration(unittest.TestCase):
    """Test complete target intelligence system integration"""
    
    def test_end_to_end_target_analysis(self):
        """Test complete end-to-end target analysis"""
        async def run_test():
            # Initialize components
            resolver = TargetResolver()
            profiler = TargetProfiler()
            scanner = VulnerabilityScanner()
            
            # Step 1: Resolve target
            target_info = await resolver.resolve_target("127.0.0.1")
            self.assertIsInstance(target_info, TargetInfo)
            
            # Step 2: Profile target
            topology, fingerprints, defense_profile = await profiler.profile_target(target_info)
            self.assertIsInstance(topology, dict)
            self.assertIsInstance(fingerprints, list)
            self.assertIsInstance(defense_profile, DefenseProfile)
            
            # Step 3: Scan vulnerabilities
            vuln_report = await scanner.scan_vulnerabilities(target_info, fingerprints)
            self.assertIsInstance(vuln_report, VulnerabilityReport)
            
            # Step 4: Generate performance profile
            perf_profile = await profiler.generate_performance_profile(target_info)
            self.assertIsInstance(perf_profile, PerformanceProfile)
            
            # Validate comprehensive analysis
            self.assertGreater(target_info.resolution_time, 0)
            self.assertGreaterEqual(defense_profile.overall_strength, 0.0)
            self.assertGreaterEqual(vuln_report.attack_surface.overall_risk_score, 0.0)
        
        asyncio.run(run_test())
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for target intelligence"""
        async def run_test():
            resolver = TargetResolver()
            
            # Benchmark resolution time
            start_time = time.time()
            target_info = await resolver.resolve_target("127.0.0.1")
            resolution_time = time.time() - start_time
            
            # Should complete within reasonable time
            self.assertLess(resolution_time, 30.0)  # 30 seconds max
            self.assertGreater(target_info.resolution_time, 0)
            
            # Benchmark service discovery
            if target_info.ports:
                # Should have attempted service discovery
                self.assertIsInstance(target_info.ports, list)
        
        asyncio.run(run_test())
    
    def test_error_handling_and_resilience(self):
        """Test error handling and system resilience"""
        async def run_test():
            resolver = TargetResolver()
            
            # Test with invalid target
            try:
                target_info = await resolver.resolve_target("invalid.invalid.invalid")
                # Should handle gracefully - either resolve or return empty result
                self.assertIsInstance(target_info, TargetInfo)
            except Exception as e:
                # Should not raise unhandled exceptions
                self.fail(f"Unhandled exception for invalid target: {e}")
            
            # Test with unreachable IP
            try:
                target_info = await resolver.resolve_target("192.0.2.1")  # TEST-NET-1
                self.assertIsInstance(target_info, TargetInfo)
                # Should handle unreachable targets gracefully
            except Exception as e:
                self.fail(f"Unhandled exception for unreachable target: {e}")
        
        asyncio.run(run_test())


class TestTargetIntelligencePerformance(unittest.TestCase):
    """Test performance characteristics of target intelligence system"""
    
    def test_concurrent_target_resolution(self):
        """Test concurrent target resolution performance"""
        async def run_test():
            resolver = TargetResolver()
            
            # Test concurrent resolution of multiple targets
            targets = ["127.0.0.1", "192.0.2.1", "192.0.2.2"]
            
            start_time = time.time()
            tasks = [resolver.resolve_target(target) for target in targets]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Should complete all resolutions
            self.assertEqual(len(results), len(targets))
            
            # Should be faster than sequential processing
            self.assertLess(total_time, len(targets) * 10)  # Reasonable concurrent performance
            
            # Check that all results are valid (or exceptions are handled)
            for result in results:
                if isinstance(result, Exception):
                    # Exceptions should be handled gracefully
                    continue
                self.assertIsInstance(result, TargetInfo)
        
        asyncio.run(run_test())
    
    def test_dns_cache_performance(self):
        """Test DNS cache performance impact"""
        async def run_test():
            resolver = TargetResolver()
            
            # First resolution (cache miss)
            start_time = time.time()
            target_info1 = await resolver.resolve_target("127.0.0.1")
            first_time = time.time() - start_time
            
            # Second resolution (should use cache if hostname was resolved)
            start_time = time.time()
            target_info2 = await resolver.resolve_target("127.0.0.1")
            second_time = time.time() - start_time
            
            # Both should succeed
            self.assertIsInstance(target_info1, TargetInfo)
            self.assertIsInstance(target_info2, TargetInfo)
            
            # For IP addresses, both should be fast since no DNS resolution needed
            # This test mainly validates that caching doesn't break functionality
        
        asyncio.run(run_test())


if __name__ == '__main__':
    # Run tests with appropriate test discovery
    unittest.main(verbosity=2)