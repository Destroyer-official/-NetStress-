"""
Real DNS query generator.

This module generates valid DNS queries per RFC 1035 specification.
Supports A, AAAA, ANY, and other query types for DNS amplification testing.
"""

import socket
import struct
import time
import logging
import random
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, field
from enum import IntEnum

logger = logging.getLogger(__name__)


class DNSQueryType(IntEnum):
    """DNS query types per RFC 1035"""
    A = 1       # IPv4 address
    NS = 2      # Name server
    CNAME = 5   # Canonical name
    SOA = 6     # Start of authority
    PTR = 12    # Pointer record
    MX = 15     # Mail exchange
    TXT = 16    # Text record
    AAAA = 28   # IPv6 address
    SRV = 33    # Service record
    ANY = 255   # Any record type


class DNSClass(IntEnum):
    """DNS classes per RFC 1035"""
    IN = 1      # Internet
    CS = 2      # CSNET (obsolete)
    CH = 3      # CHAOS
    HS = 4      # Hesiod


@dataclass
class DNSQueryStats:
    """Statistics for DNS queries"""
    queries_sent: int = 0
    responses_received: int = 0
    queries_failed: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    response_codes: Dict[int, int] = field(default_factory=dict)
    amplification_ratios: List[float] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def queries_per_second(self) -> float:
        if self.duration > 0:
            return self.queries_sent / self.duration
        return 0.0
    
    @property
    def success_rate(self) -> float:
        if self.queries_sent > 0:
            return self.responses_received / self.queries_sent
        return 0.0
    
    @property
    def average_amplification(self) -> float:
        if self.amplification_ratios:
            return sum(self.amplification_ratios) / len(self.amplification_ratios)
        return 0.0


class RealDNSGenerator:
    """
    Real DNS query generator using valid DNS protocol.
    
    Generates RFC 1035 compliant DNS queries with proper packet structure.
    Supports various query types for legitimate DNS testing and amplification research.
    """
    
    def __init__(self, dns_server: str, dns_port: int = 53, source_port: Optional[int] = None):
        """
        Initialize DNS generator.
        
        Args:
            dns_server: DNS server IP address
            dns_port: DNS server port (default 53)
            source_port: Source port (random if None)
        """
        self.dns_server = dns_server
        self.dns_port = dns_port
        self.source_port = source_port or random.randint(1024, 65535)
        self.socket = None
        self.stats = DNSQueryStats()
        self.transaction_id = random.randint(1, 65535)
        
    def __enter__(self):
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def open(self) -> None:
        """Open UDP socket for DNS queries"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('', self.source_port))
            self.socket.settimeout(5.0)  # 5 second timeout for responses
            
            logger.info(f"DNS generator opened: {self.dns_server}:{self.dns_port}")
            
        except Exception as e:
            logger.error(f"Failed to open DNS socket: {e}")
            raise
            
    def close(self) -> None:
        """Close DNS socket"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("DNS generator closed")
            except Exception as e:
                logger.warning(f"Error closing DNS socket: {e}")
            finally:
                self.socket = None
                
    def _encode_domain_name(self, domain: str) -> bytes:
        """
        Encode domain name in DNS format.
        
        DNS names are encoded as length-prefixed labels.
        Example: "example.com" -> b"\x07example\x03com\x00"
        """
        if not domain:
            return b'\x00'
            
        encoded = b''
        for label in domain.split('.'):
            if len(label) > 63:
                raise ValueError(f"DNS label too long: {label}")
            encoded += bytes([len(label)]) + label.encode('ascii')
        encoded += b'\x00'  # Null terminator
        return encoded
        
    def _create_dns_query(self, domain: str, query_type: DNSQueryType = DNSQueryType.A,
                         query_class: DNSClass = DNSClass.IN, recursion_desired: bool = True) -> bytes:
        """
        Create DNS query packet per RFC 1035.
        
        Args:
            domain: Domain name to query
            query_type: DNS query type (A, AAAA, ANY, etc.)
            query_class: DNS class (usually IN for Internet)
            recursion_desired: Set RD flag
            
        Returns:
            Complete DNS query packet
        """
        # DNS Header (12 bytes)
        transaction_id = self.transaction_id
        self.transaction_id = (self.transaction_id + 1) % 65536
        
        # Flags: QR=0 (query), Opcode=0 (standard), AA=0, TC=0, RD=1, RA=0, Z=0, RCODE=0
        flags = 0x0000
        if recursion_desired:
            flags |= 0x0100  # Set RD bit
            
        qdcount = 1  # Number of questions
        ancount = 0  # Number of answers
        nscount = 0  # Number of authority records
        arcount = 0  # Number of additional records
        
        header = struct.pack('!HHHHHH',
                           transaction_id,
                           flags,
                           qdcount,
                           ancount,
                           nscount,
                           arcount)
        
        # Question section
        qname = self._encode_domain_name(domain)
        qtype = int(query_type)
        qclass = int(query_class)
        
        question = qname + struct.pack('!HH', qtype, qclass)
        
        return header + question
        
    def _parse_dns_response(self, response_data: bytes) -> Dict[str, Any]:
        """
        Parse DNS response packet.
        
        Args:
            response_data: Raw DNS response
            
        Returns:
            Parsed response information
        """
        if len(response_data) < 12:
            return {'error': 'Response too short'}
            
        try:
            # Parse header
            header = struct.unpack('!HHHHHH', response_data[:12])
            transaction_id, flags, qdcount, ancount, nscount, arcount = header
            
            # Extract response code
            rcode = flags & 0x000F
            
            return {
                'transaction_id': transaction_id,
                'response_code': rcode,
                'answer_count': ancount,
                'authority_count': nscount,
                'additional_count': arcount,
                'size': len(response_data)
            }
            
        except Exception as e:
            return {'error': f'Parse error: {e}'}
            
    def send_query(self, domain: str, query_type: DNSQueryType = DNSQueryType.A,
                  wait_for_response: bool = True) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send a single DNS query.
        
        Args:
            domain: Domain name to query
            query_type: DNS query type
            wait_for_response: Whether to wait for and parse response
            
        Returns:
            Tuple of (success, response_info)
        """
        if not self.socket:
            logger.error("Socket not opened")
            return False, None
            
        try:
            # Create and send query
            query_packet = self._create_dns_query(domain, query_type)
            bytes_sent = self.socket.sendto(query_packet, (self.dns_server, self.dns_port))
            
            self.stats.queries_sent += 1
            self.stats.bytes_sent += bytes_sent
            
            logger.debug(f"Sent DNS query for {domain} ({query_type.name}): {bytes_sent} bytes")
            
            if not wait_for_response:
                return True, None
                
            # Wait for response
            try:
                response_data, addr = self.socket.recvfrom(4096)
                self.stats.responses_received += 1
                self.stats.bytes_received += len(response_data)
                
                # Calculate amplification ratio
                if bytes_sent > 0:
                    amplification = len(response_data) / bytes_sent
                    self.stats.amplification_ratios.append(amplification)
                
                # Parse response
                response_info = self._parse_dns_response(response_data)
                
                # Track response codes
                if 'response_code' in response_info:
                    rcode = response_info['response_code']
                    if rcode in self.stats.response_codes:
                        self.stats.response_codes[rcode] += 1
                    else:
                        self.stats.response_codes[rcode] = 1
                
                logger.debug(f"Received DNS response: {len(response_data)} bytes, "
                           f"amplification {amplification:.2f}x")
                
                return True, response_info
                
            except socket.timeout:
                logger.debug(f"DNS query timeout for {domain}")
                self.stats.queries_failed += 1
                return False, None
                
        except Exception as e:
            logger.warning(f"DNS query failed for {domain}: {e}")
            self.stats.queries_failed += 1
            return False, None
            
    def send_amplification_test(self, target_domains: List[str], 
                               query_types: List[DNSQueryType] = None,
                               queries_per_domain: int = 1) -> DNSQueryStats:
        """
        Test DNS amplification potential.
        
        Args:
            target_domains: List of domains to query
            query_types: List of query types to test (default: A, ANY, TXT)
            queries_per_domain: Number of queries per domain/type combination
            
        Returns:
            Amplification test statistics
        """
        if not self.socket:
            raise RuntimeError("Socket not opened")
            
        if query_types is None:
            query_types = [DNSQueryType.A, DNSQueryType.ANY, DNSQueryType.TXT]
            
        test_stats = DNSQueryStats()
        test_stats.start_time = time.perf_counter()
        
        logger.info(f"Starting DNS amplification test: {len(target_domains)} domains, "
                   f"{len(query_types)} query types, {queries_per_domain} queries each")
        
        for domain in target_domains:
            for query_type in query_types:
                for _ in range(queries_per_domain):
                    success, response = self.send_query(domain, query_type, wait_for_response=True)
                    
                    if success and response:
                        test_stats.queries_sent += 1
                        test_stats.responses_received += 1
                        test_stats.bytes_sent += self.stats.bytes_sent
                        test_stats.bytes_received += self.stats.bytes_received
                        
                        if self.stats.amplification_ratios:
                            test_stats.amplification_ratios.append(self.stats.amplification_ratios[-1])
                    else:
                        test_stats.queries_sent += 1
                        test_stats.queries_failed += 1
                        
        test_stats.end_time = time.perf_counter()
        
        logger.info(f"DNS amplification test complete: {test_stats.responses_received}/{test_stats.queries_sent} successful, "
                   f"average amplification {test_stats.average_amplification:.2f}x")
        
        return test_stats
        
    def send_query_flood(self, domain: str, query_count: int,
                        query_type: DNSQueryType = DNSQueryType.A,
                        delay_ms: float = 0, wait_for_responses: bool = False) -> DNSQueryStats:
        """
        Send DNS query flood.
        
        Args:
            domain: Domain to query
            query_count: Number of queries to send
            query_type: DNS query type
            delay_ms: Delay between queries in milliseconds
            wait_for_responses: Whether to wait for responses
            
        Returns:
            Query flood statistics
        """
        if not self.socket:
            raise RuntimeError("Socket not opened")
            
        flood_stats = DNSQueryStats()
        flood_stats.start_time = time.perf_counter()
        
        logger.info(f"Starting DNS query flood: {query_count} queries for {domain} ({query_type.name})")
        
        for i in range(query_count):
            success, response = self.send_query(domain, query_type, wait_for_responses)
            
            if success:
                flood_stats.queries_sent += 1
                if response:
                    flood_stats.responses_received += 1
            else:
                flood_stats.queries_failed += 1
                
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
                
        flood_stats.end_time = time.perf_counter()
        
        # Copy accumulated stats
        flood_stats.bytes_sent = self.stats.bytes_sent
        flood_stats.bytes_received = self.stats.bytes_received
        flood_stats.response_codes = self.stats.response_codes.copy()
        flood_stats.amplification_ratios = self.stats.amplification_ratios.copy()
        
        logger.info(f"DNS query flood complete: {flood_stats.queries_sent} queries sent, "
                   f"{flood_stats.queries_per_second:.1f} QPS")
        
        return flood_stats
        
    def generate_random_subdomain(self, base_domain: str, subdomain_length: int = 8) -> str:
        """Generate random subdomain for varied queries"""
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        subdomain = ''.join(random.choice(chars) for _ in range(subdomain_length))
        return f"{subdomain}.{base_domain}"
        
    def get_amplification_domains(self) -> List[str]:
        """
        Get list of domains known for high DNS amplification.
        
        Note: These are for research/testing purposes only.
        Use responsibly and only against your own infrastructure.
        """
        return [
            # Root servers (usually have large responses for ANY queries)
            'a.root-servers.net',
            'b.root-servers.net',
            'c.root-servers.net',
            # Large TXT records
            'google.com',
            'microsoft.com',
            'amazon.com',
            # Domains with many subdomains
            'github.com',
            'stackoverflow.com'
        ]
        
    def get_stats(self) -> DNSQueryStats:
        """Get current statistics"""
        return self.stats


def create_dns_generator(dns_server: str, dns_port: int = 53, 
                        source_port: Optional[int] = None) -> RealDNSGenerator:
    """
    Factory function to create DNS generator.
    
    Args:
        dns_server: DNS server IP address
        dns_port: DNS server port (default 53)
        source_port: Source port (random if None)
        
    Returns:
        Configured DNS generator
    """
    return RealDNSGenerator(dns_server, dns_port, source_port)