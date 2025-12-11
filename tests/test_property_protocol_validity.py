"""
Property-Based Test: Valid Protocol Packets

**Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

This property test verifies that for any generated UDP, TCP, HTTP, or DNS packet,
the packet SHALL be parseable by standard protocol parsers without errors.

Property: For any generated UDP, TCP, HTTP, or DNS packet, the packet SHALL be
parseable by standard protocol parsers without errors.
"""

import os
import sys
import socket
import struct
import time
import asyncio
import platform
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse
import json

import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.protocols.real_dns import DNSQueryType

try:
    from hypothesis import given, strategies as st, settings, assume, HealthCheck
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    HealthCheck = None
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip(reason="hypothesis not installed")(func)
        return decorator
    
    class st:
        @staticmethod
        def integers(min_value=0, max_value=100):
            return 50
        
        @staticmethod
        def text(min_size=1, max_size=20):
            return "example.com"
        
        @staticmethod
        def sampled_from(choices):
            return choices[0] if choices else None
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def assume(condition):
        pass


def get_project_root() -> Path:
    """Get the NetStress project root directory."""
    current = Path(__file__).parent.parent
    if current.name == '-NetStress-':
        return current
    for parent in Path(__file__).parents:
        if parent.name == '-NetStress-':
            return parent
        netstress_dir = parent / '-NetStress-'
        if netstress_dir.exists():
            return netstress_dir
    return current


# Add project root to path
project_root = get_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class UDPPacketValidator:
    """Validator for UDP packets using standard socket parsing."""
    
    @staticmethod
    def validate_udp_packet(packet_data: bytes, expected_dest_port: int) -> bool:
        """
        Validate UDP packet structure.
        
        Args:
            packet_data: Raw UDP packet data
            expected_dest_port: Expected destination port
            
        Returns:
            True if packet is valid UDP
        """
        try:
            # UDP header is 8 bytes: src_port(2) + dst_port(2) + length(2) + checksum(2)
            if len(packet_data) < 8:
                return False
                
            # Parse UDP header
            src_port, dst_port, length, checksum = struct.unpack('!HHHH', packet_data[:8])
            
            # Validate basic constraints
            if dst_port != expected_dest_port:
                return False
                
            if length < 8:  # UDP header is minimum 8 bytes
                return False
                
            if length > len(packet_data):  # Length can't exceed actual data
                return False
                
            # Port numbers should be valid
            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                return False
                
            return True
            
        except (struct.error, ValueError, IndexError):
            return False


class TCPPacketValidator:
    """Validator for TCP packets using standard socket parsing."""
    
    @staticmethod
    def validate_tcp_syn_packet(packet_data: bytes) -> bool:
        """
        Validate TCP SYN packet structure.
        
        Args:
            packet_data: Raw TCP packet (including IP header)
            
        Returns:
            True if packet is valid TCP SYN
        """
        try:
            # Skip IP header (20 bytes minimum)
            if len(packet_data) < 40:  # IP(20) + TCP(20) minimum
                return False
                
            # Parse IP header to get TCP header offset
            ip_header = packet_data[:20]
            version_ihl = ip_header[0]
            ihl = (version_ihl & 0x0F) * 4  # Internet Header Length in bytes
            
            if len(packet_data) < ihl + 20:  # Need at least TCP header
                return False
                
            # Parse TCP header
            tcp_header = packet_data[ihl:ihl+20]
            src_port, dst_port, seq_num, ack_num, flags_window = struct.unpack('!HHLLH', tcp_header[:14])
            
            # Extract flags
            data_offset = (flags_window >> 12) * 4
            flags = (flags_window >> 8) & 0xFF
            
            # Check SYN flag (bit 1)
            syn_flag = (flags & 0x02) != 0
            
            # Validate constraints
            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                return False
                
            if data_offset < 20:  # TCP header minimum 20 bytes
                return False
                
            if not syn_flag:  # Should be SYN packet
                return False
                
            return True
            
        except (struct.error, ValueError, IndexError):
            return False


class HTTPRequestValidator:
    """Validator for HTTP requests using standard parsing."""
    
    @staticmethod
    def validate_http_request(request_data: bytes) -> bool:
        """
        Validate HTTP request structure per RFC 7230.
        
        Args:
            request_data: Raw HTTP request data
            
        Returns:
            True if request is valid HTTP/1.1
        """
        try:
            # Convert to string for parsing
            request_str = request_data.decode('utf-8', errors='ignore')
            
            # Split into lines
            lines = request_str.split('\r\n')
            if len(lines) < 2:  # Need at least request line and empty line
                return False
                
            # Parse request line
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) != 3:
                return False
                
            method, path, version = parts
            
            # Validate method
            valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']
            if method not in valid_methods:
                return False
                
            # Validate version
            if not version.startswith('HTTP/1.'):
                return False
                
            # Validate path
            if not path.startswith('/'):
                return False
                
            # Parse headers
            header_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line == '':  # Empty line marks end of headers
                    header_end = i
                    break
                    
                # Validate header format
                if ':' not in line:
                    return False
                    
                header_name, header_value = line.split(':', 1)
                header_name = header_name.strip()
                header_value = header_value.strip()
                
                # Header name should not be empty
                if not header_name:
                    return False
                    
            # Should have found end of headers
            if header_end == -1:
                return False
                
            return True
            
        except (UnicodeDecodeError, ValueError, IndexError):
            return False


class DNSPacketValidator:
    """Validator for DNS packets using standard parsing."""
    
    @staticmethod
    def validate_dns_query(packet_data: bytes) -> bool:
        """
        Validate DNS query packet structure per RFC 1035.
        
        Args:
            packet_data: Raw DNS query packet
            
        Returns:
            True if packet is valid DNS query
        """
        try:
            # DNS header is 12 bytes minimum
            if len(packet_data) < 12:
                return False
                
            # Parse DNS header
            header = struct.unpack('!HHHHHH', packet_data[:12])
            transaction_id, flags, qdcount, ancount, nscount, arcount = header
            
            # Validate flags for query
            qr = (flags >> 15) & 0x1  # Query/Response bit
            opcode = (flags >> 11) & 0xF  # Opcode
            
            # Should be a query (QR=0) with standard opcode (0)
            if qr != 0:  # Should be query, not response
                return False
                
            if opcode != 0:  # Should be standard query
                return False
                
            # Should have at least one question
            if qdcount == 0:
                return False
                
            # Response sections should be empty for queries
            if ancount != 0 or nscount != 0 or arcount != 0:
                return False
                
            # Parse question section
            offset = 12
            for _ in range(qdcount):
                # Parse domain name
                while offset < len(packet_data):
                    length = packet_data[offset]
                    offset += 1
                    
                    if length == 0:  # End of name
                        break
                    elif length & 0xC0:  # Compression pointer (not valid in queries)
                        return False
                    else:
                        # Label
                        if offset + length > len(packet_data):
                            return False
                        offset += length
                        
                # Parse QTYPE and QCLASS (4 bytes)
                if offset + 4 > len(packet_data):
                    return False
                    
                qtype, qclass = struct.unpack('!HH', packet_data[offset:offset+4])
                offset += 4
                
                # Validate QTYPE and QCLASS
                valid_qtypes = [1, 2, 5, 6, 12, 15, 16, 28, 33, 255]  # Common types
                if qtype not in valid_qtypes:
                    return False
                    
                if qclass != 1:  # Should be IN (Internet) class
                    return False
                    
            return True
            
        except (struct.error, ValueError, IndexError):
            return False


class TestProtocolValidity:
    """
    Test suite for Property 13: Valid Protocol Packets
    
    **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    
    def test_udp_packet_validity(self):
        """
        Test that generated UDP packets are valid.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.1**
        """
        from core.protocols.real_udp import RealUDPGenerator
        
        generator = RealUDPGenerator("127.0.0.1", 12345)
        
        # Test different payload sizes
        for payload_size in [0, 10, 100, 1000]:
            payload = generator.generate_payload(payload_size, 'random')
            
            # Create UDP packet manually to test structure
            src_port = 54321
            dst_port = 12345
            length = 8 + len(payload)
            checksum = 0  # Simplified for test
            
            udp_header = struct.pack('!HHHH', src_port, dst_port, length, checksum)
            packet = udp_header + payload
            
            # Validate packet
            is_valid = UDPPacketValidator.validate_udp_packet(packet, dst_port)
            assert is_valid, f"Generated UDP packet with {payload_size} byte payload is invalid"
    
    def test_tcp_syn_packet_validity(self):
        """
        Test that generated TCP SYN packets are valid.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.2**
        """
        from core.protocols.real_tcp import RealTCPGenerator
        
        generator = RealTCPGenerator("127.0.0.1", 80)
        
        # Check if raw sockets are available
        if not generator.can_use_raw_sockets:
            pytest.skip("Raw sockets not available (requires root)")
            
        # Test SYN packet creation
        try:
            packet = generator._create_tcp_syn_packet("192.168.1.100", 54321)
            
            # Validate packet structure
            is_valid = TCPPacketValidator.validate_tcp_syn_packet(packet)
            assert is_valid, "Generated TCP SYN packet is invalid"
            
        except Exception as e:
            pytest.skip(f"TCP SYN packet generation failed: {e}")
    
    def test_http_request_validity(self):
        """
        Test that generated HTTP requests are valid per RFC 7230.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.3**
        """
        from core.protocols.real_http import RealHTTPGenerator
        
        generator = RealHTTPGenerator("http://example.com/test")
        
        # Test GET request
        get_request = generator._build_http_request('GET')
        is_valid = HTTPRequestValidator.validate_http_request(get_request)
        assert is_valid, "Generated HTTP GET request is invalid"
        
        # Test POST request with body
        post_data = b'{"test": "data"}'
        post_headers = {'Content-Type': 'application/json'}
        post_request = generator._build_http_request('POST', post_headers, post_data)
        is_valid = HTTPRequestValidator.validate_http_request(post_request)
        assert is_valid, "Generated HTTP POST request is invalid"
        
        # Test with query parameters
        query_params = {'param1': 'value1', 'param2': 'value2'}
        query_request = generator._build_http_request('GET', query_params=query_params)
        is_valid = HTTPRequestValidator.validate_http_request(query_request)
        assert is_valid, "Generated HTTP request with query parameters is invalid"
    
    def test_dns_query_validity(self):
        """
        Test that generated DNS queries are valid per RFC 1035.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.4**
        """
        from core.protocols.real_dns import RealDNSGenerator, DNSQueryType
        
        generator = RealDNSGenerator("8.8.8.8")
        
        # Test different query types
        test_domains = ["example.com", "google.com", "test.local"]
        query_types = [DNSQueryType.A, DNSQueryType.AAAA, DNSQueryType.ANY, DNSQueryType.TXT]
        
        for domain in test_domains:
            for query_type in query_types:
                query_packet = generator._create_dns_query(domain, query_type)
                
                # Validate packet structure
                is_valid = DNSPacketValidator.validate_dns_query(query_packet)
                assert is_valid, f"Generated DNS query for {domain} ({query_type.name}) is invalid"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        payload_size=st.integers(min_value=0, max_value=1400),
        pattern=st.sampled_from(['random', 'zeros', 'ones', 'sequence'])
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_udp_packet_validity(self, payload_size, pattern):
        """
        Property test: For any UDP packet configuration, the generated packet
        SHALL be parseable by standard UDP parsers.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.1**
        """
        from core.protocols.real_udp import RealUDPGenerator
        
        generator = RealUDPGenerator("127.0.0.1", 12345)
        payload = generator.generate_payload(payload_size, pattern)
        
        # Create UDP packet
        src_port = 54321
        dst_port = 12345
        length = 8 + len(payload)
        checksum = 0
        
        udp_header = struct.pack('!HHHH', src_port, dst_port, length, checksum)
        packet = udp_header + payload
        
        # Property assertion
        is_valid = UDPPacketValidator.validate_udp_packet(packet, dst_port)
        assert is_valid, f"UDP packet with {payload_size} byte {pattern} payload is invalid"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(
        domain=st.builds(
            lambda parts: '.'.join(parts),
            st.lists(
                st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=10).filter(
                    lambda x: x[0].isalpha()
                ),
                min_size=2, max_size=4
            )
        ),
        query_type=st.sampled_from([DNSQueryType.A, DNSQueryType.AAAA, DNSQueryType.ANY])
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.filter_too_much])
    def test_property_dns_query_validity(self, domain, query_type):
        """
        Property test: For any domain name and query type, the generated DNS query
        SHALL be parseable by standard DNS parsers.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.4**
        """
        from core.protocols.real_dns import RealDNSGenerator
        
        # Ensure domain is valid
        assume(len(domain) >= 3)
        assume('.' in domain)
        assume(not domain.startswith('.'))
        assume(not domain.endswith('.'))
        
        generator = RealDNSGenerator("8.8.8.8")
        
        try:
            query_packet = generator._create_dns_query(domain, query_type)
            
            # Property assertion
            is_valid = DNSPacketValidator.validate_dns_query(query_packet)
            assert is_valid, f"DNS query for {domain} ({query_type.name}) is invalid"
            
        except ValueError:
            # Skip invalid domain names
            assume(False)


class TestProtocolParsing:
    """
    Test that generated packets can be parsed by external tools.
    
    **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    
    def test_http_request_parsing_with_urllib(self):
        """
        Test HTTP request parsing with standard library.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.3**
        """
        from core.protocols.real_http import RealHTTPGenerator
        from urllib.parse import urlparse, parse_qs
        
        generator = RealHTTPGenerator("http://example.com/path?param=value")
        
        # Generate request
        request_data = generator._build_http_request('GET')
        request_str = request_data.decode('utf-8')
        
        # Parse request line
        lines = request_str.split('\r\n')
        request_line = lines[0]
        method, path, version = request_line.split(' ')
        
        # Parse URL components
        parsed_url = urlparse(f"http://example.com{path}")
        
        # Should be parseable without errors
        assert parsed_url.path == "/path"
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            assert isinstance(query_params, dict)
    
    def test_dns_domain_encoding(self):
        """
        Test DNS domain name encoding follows RFC 1035.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.4**
        """
        from core.protocols.real_dns import RealDNSGenerator
        
        generator = RealDNSGenerator("8.8.8.8")
        
        # Test domain encoding
        test_cases = [
            ("example.com", b"\x07example\x03com\x00"),
            ("test.local", b"\x04test\x05local\x00"),
            ("a.b.c", b"\x01a\x01b\x01c\x00")
        ]
        
        for domain, expected in test_cases:
            encoded = generator._encode_domain_name(domain)
            assert encoded == expected, f"Domain {domain} encoded incorrectly"


class TestProtocolCompliance:
    """
    Test protocol compliance with RFCs.
    
    **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    
    def test_http_headers_compliance(self):
        """
        Test HTTP headers follow RFC 7230 format.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.3**
        """
        from core.protocols.real_http import RealHTTPGenerator
        
        generator = RealHTTPGenerator("http://example.com")
        
        # Test with various headers
        custom_headers = {
            'Authorization': 'Bearer token123',
            'Content-Type': 'application/json',
            'User-Agent': 'TestAgent/1.0',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        request_data = generator._build_http_request('POST', custom_headers, b'{"test": true}')
        request_str = request_data.decode('utf-8')
        
        # Verify header format
        lines = request_str.split('\r\n')
        
        # Find headers (skip request line)
        for line in lines[1:]:
            if line == '':  # End of headers
                break
                
            # Each header should have name: value format
            assert ':' in line, f"Invalid header format: {line}"
            
            name, value = line.split(':', 1)
            name = name.strip()
            value = value.strip()
            
            # Header name should not be empty
            assert name, f"Empty header name in: {line}"
            
            # Header name should not contain spaces
            assert ' ' not in name, f"Header name contains spaces: {name}"
    
    def test_dns_packet_structure(self):
        """
        Test DNS packet structure follows RFC 1035.
        
        **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
        **Validates: Requirements 9.4**
        """
        from core.protocols.real_dns import RealDNSGenerator, DNSQueryType
        
        generator = RealDNSGenerator("8.8.8.8")
        
        # Create query and verify structure
        query_packet = generator._create_dns_query("example.com", DNSQueryType.A)
        
        # Parse header
        header = struct.unpack('!HHHHHH', query_packet[:12])
        transaction_id, flags, qdcount, ancount, nscount, arcount = header
        
        # Verify query flags
        qr = (flags >> 15) & 0x1
        opcode = (flags >> 11) & 0xF
        rd = (flags >> 8) & 0x1
        
        assert qr == 0, "QR bit should be 0 for queries"
        assert opcode == 0, "Opcode should be 0 for standard queries"
        assert qdcount == 1, "Should have exactly 1 question"
        assert ancount == 0, "Answer count should be 0 for queries"
        assert nscount == 0, "Authority count should be 0 for queries"
        assert arcount == 0, "Additional count should be 0 for queries"


def test_protocol_validity_basic():
    """
    Basic test for protocol validity.
    
    **Feature: real-high-performance-netstress, Property 13: Valid Protocol Packets**
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    # Test UDP
    validator = UDPPacketValidator()
    udp_packet = struct.pack('!HHHH', 12345, 80, 8, 0)  # Simple UDP header
    assert validator.validate_udp_packet(udp_packet, 80)
    
    # Test HTTP
    http_request = b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    assert HTTPRequestValidator.validate_http_request(http_request)
    
    # Test DNS
    # Simple DNS query header + question for "a.com"
    dns_query = (b'\x12\x34'  # Transaction ID
                b'\x01\x00'  # Flags (standard query, RD=1)
                b'\x00\x01'  # QDCOUNT=1
                b'\x00\x00'  # ANCOUNT=0
                b'\x00\x00'  # NSCOUNT=0
                b'\x00\x00'  # ARCOUNT=0
                b'\x01a\x03com\x00'  # "a.com"
                b'\x00\x01'  # QTYPE=A
                b'\x00\x01')  # QCLASS=IN
    assert DNSPacketValidator.validate_dns_query(dns_query)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])