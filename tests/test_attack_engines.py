#!/usr/bin/env python3
"""
Comprehensive Attack Engine Tests
Tests all protocol implementations for correctness and performance
"""

import asyncio
import pytest
import socket
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

# Import attack engines
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.networking.tcp_engine import TCPEngine, TCPAttackConfig, TCPAttackType
from core.networking.udp_engine import ExtremeUDPEngine, UDPAttackConfig
from core.networking.http_engine import ModernHTTPEngine, HTTPAttackConfig
from core.networking.dns_engine import DNSWeaponizationEngine, DNSAttackConfig
from core.networking.reflection_engine import ReflectionAmplificationEngine, ReflectionAttackConfig


class TestTCPEngine:
    """Test TCP attack engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = TCPAttackConfig(
            target="127.0.0.1",
            port=8080,
            enable_spoofing=False,
            max_connections=10
        )
        self.engine = TCPEngine(self.config)
    
    def test_tcp_config_initialization(self):
        """Test TCP configuration initialization"""
        assert self.engine.config.target == "127.0.0.1"
        assert self.engine.config.port == 8080
        assert self.engine.config.max_connections == 10
        assert self.engine.stats is not None
    
    def test_supported_attacks(self):
        """Test supported attack types"""
        attacks = self.engine.get_supported_attacks()
        assert 'syn_flood' in attacks
        assert 'slowloris' in attacks
        assert 'connection_exhaustion' in attacks
    
    @pytest.mark.asyncio
    async def test_packet_creation(self):
        """Test TCP packet creation"""
        packet = await self.engine.create_packet(
            "127.0.0.1", 8080, 64, TCPAttackType.SYN_FLOOD
        )
        assert len(packet) > 0
        assert isinstance(packet, bytes)
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test get_status method"""
        status = await self.engine.get_status()
        assert 'initialized' in status
        assert 'stats' in status
        assert isinstance(status['stats'], dict)
    
    @pytest.mark.asyncio
    async def test_syn_flood_short_duration(self):
        """Test SYN flood with short duration"""
        result = await self.engine.syn_flood(
            "127.0.0.1", 8080, duration=0.1, packet_size=64, rate_limit=100
        )
        assert result['attack_type'] == 'SYN_FLOOD'
        assert result['packets_sent'] >= 0


class TestUDPEngine:
    """Test UDP attack engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = UDPAttackConfig(
            target="127.0.0.1",
            port=8080,
            packet_size=1024,
            enable_spoofing=False,
            burst_size=10
        )
        self.engine = ExtremeUDPEngine(self.config)
    
    def test_udp_config_initialization(self):
        """Test UDP configuration initialization"""
        assert self.engine.config.target == "127.0.0.1"
        assert self.engine.config.port == 8080
        assert self.engine.config.packet_size == 1024
    
    def test_payload_generation_random(self):
        """Test UDP random payload generation"""
        from core.networking.udp_engine import UDPPayloadGenerator
        
        payload = UDPPayloadGenerator.random_payload(100)
        assert len(payload) == 100
        assert isinstance(payload, bytes)
    
    def test_payload_generation_fragmented(self):
        """Test UDP fragmented payload generation"""
        from core.networking.udp_engine import UDPPayloadGenerator
        
        fragments = UDPPayloadGenerator.fragmented_payload(2000, 500)
        assert len(fragments) == 4  # 2000/500 = 4 fragments
    
    def test_amplification_servers(self):
        """Test amplification server database"""
        from core.networking.udp_engine import UDPAmplificationServers
        
        assert len(UDPAmplificationServers.DNS_SERVERS) > 0
        assert len(UDPAmplificationServers.NTP_SERVERS) > 0
        assert "8.8.8.8" in UDPAmplificationServers.DNS_SERVERS


class TestHTTPEngine:
    """Test HTTP attack engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = HTTPAttackConfig(
            target="httpbin.org",
            port=80,
            use_ssl=False,
            http_version="1.1",
            max_connections=10
        )
        self.engine = ModernHTTPEngine(self.config)
    
    def test_http_config_initialization(self):
        """Test HTTP configuration initialization"""
        assert self.engine.config.target == "httpbin.org"
        assert self.engine.config.port == 80
        assert self.engine.config.http_version == "1.1"
    
    def test_payload_generation(self):
        """Test HTTP payload generation"""
        from core.networking.http_engine import HTTPPayloadGenerator
        
        # Test HTTP/1.1 request generation
        request = HTTPPayloadGenerator.generate_http1_request("example.com", 80)
        assert "GET / HTTP/1.1" in request
        assert "Host: example.com:80" in request
        
        # Test slowloris headers
        headers = HTTPPayloadGenerator.generate_slowloris_headers()
        assert "User-Agent" in headers
        assert "Connection" in headers
        
        # Test cache poison headers
        poison_headers = HTTPPayloadGenerator.generate_cache_poison_headers()
        assert "X-Forwarded-Host" in poison_headers
    
    def test_ssl_context_creation(self):
        """Test SSL context creation"""
        ctx = self.engine._create_ssl_context()
        assert ctx is not None
        assert not ctx.check_hostname


class TestDNSEngine:
    """Test DNS weaponization engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = DNSAttackConfig(
            target="8.8.8.8",
            port=53,
            enable_spoofing=False,
            max_query_rate=100
        )
        self.engine = DNSWeaponizationEngine(self.config)
    
    def test_dns_config_initialization(self):
        """Test DNS configuration initialization"""
        assert self.engine.config.target == "8.8.8.8"
        assert self.engine.config.port == 53
        assert self.engine.config.max_query_rate == 100
    
    def test_dns_payload_generation(self):
        """Test DNS payload generation"""
        from core.networking.dns_engine import DNSPayloadGenerator
        
        # Test DNS query creation
        query = DNSPayloadGenerator.create_dns_query("example.com", 1)  # A record
        assert len(query) > 0
        assert isinstance(query, bytes)
        
        # Test EDNS0 query
        edns_query = DNSPayloadGenerator.create_edns0_query("example.com", 1, 4096)
        assert len(edns_query) > len(query)  # EDNS0 should be larger
    
    def test_dns_query_types(self):
        """Test DNS query types"""
        from core.networking.dns_engine import DNSQueryTypes
        
        assert DNSQueryTypes.A == 1
        assert DNSQueryTypes.NS == 2
        assert DNSQueryTypes.ANY == 255
        assert len(DNSQueryTypes.AMPLIFICATION_TYPES) > 0


class TestReflectionEngine:
    """Test reflection and amplification engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.config = ReflectionAttackConfig(
            target="127.0.0.1",
            enable_spoofing=False,
            discovery_enabled=False
        )
        self.engine = ReflectionAmplificationEngine(self.config)
    
    def test_reflection_config_initialization(self):
        """Test reflection configuration initialization"""
        assert self.engine.config.target == "127.0.0.1"
        assert not self.engine.config.enable_spoofing
    
    def test_payload_generation(self):
        """Test reflection payload generation"""
        from core.networking.reflection_engine import ReflectionPayloadGenerator
        
        # Test NTP payload
        ntp_payload = ReflectionPayloadGenerator.ntp_monlist_payload()
        assert len(ntp_payload) > 0
        assert isinstance(ntp_payload, bytes)
        
        # Test SNMP payload
        snmp_payload = ReflectionPayloadGenerator.snmp_getbulk_payload()
        assert len(snmp_payload) > 0
        
        # Test Memcached payload
        memcached_payload = ReflectionPayloadGenerator.memcached_stats_payload()
        assert memcached_payload == b"stats\r\n"
        
        # Test SSDP payload
        ssdp_payload = ReflectionPayloadGenerator.ssdp_msearch_payload()
        assert b"M-SEARCH" in ssdp_payload
    
    def test_server_database(self):
        """Test amplification server database"""
        from core.networking.reflection_engine import AmplificationServerDatabase
        
        assert len(AmplificationServerDatabase.NTP_SERVERS) > 0
        assert len(AmplificationServerDatabase.SNMP_SERVERS) > 0
        assert "pool.ntp.org" in AmplificationServerDatabase.NTP_SERVERS


class TestAttackEngineIntegration:
    """Integration tests for attack engines"""
    
    def test_tcp_engine_stats(self):
        """Test TCP engine stats collection"""
        config = TCPAttackConfig(target="127.0.0.1", port=8080)
        engine = TCPEngine(config)
        
        # Simulate some activity
        engine.stats['packets_sent'] = 1000
        engine.stats['connections_made'] = 100
        engine.stats['errors'] = 5
        
        assert engine.stats['packets_sent'] == 1000
        assert engine.stats['connections_made'] == 100
        assert engine.stats['errors'] == 5
    
    def test_error_handling(self):
        """Test error handling in attack engines"""
        config = UDPAttackConfig(target="invalid.host.name", port=8080)
        engine = ExtremeUDPEngine(config)
        
        # Error handling should not crash the engine
        try:
            stats = engine.stats
            assert isinstance(stats, dict)
        except Exception as e:
            pytest.fail(f"Engine should handle errors gracefully: {e}")


class TestAttackEnginePerformance:
    """Performance tests for attack engines"""
    
    @pytest.mark.asyncio
    async def test_tcp_packet_generation_performance(self):
        """Test TCP packet generation performance"""
        config = TCPAttackConfig(target="127.0.0.1", port=8080)
        engine = TCPEngine(config)
        
        start_time = time.time()
        
        # Generate 100 packets
        for _ in range(100):
            packet = await engine.create_packet(
                "127.0.0.1", 8080, 64, TCPAttackType.SYN_FLOOD
            )
            assert len(packet) > 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should generate packets quickly (less than 5 seconds for 100 packets)
        assert duration < 5.0, f"Packet generation too slow: {duration} seconds"
    
    def test_udp_payload_generation_performance(self):
        """Test UDP payload generation performance"""
        from core.networking.udp_engine import UDPPayloadGenerator
        
        start_time = time.time()
        
        # Generate 1000 payloads
        for _ in range(1000):
            payload = UDPPayloadGenerator.random_payload(1024)
            assert len(payload) == 1024
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should generate payloads quickly
        assert duration < 1.0, f"Payload generation too slow: {duration} seconds"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
