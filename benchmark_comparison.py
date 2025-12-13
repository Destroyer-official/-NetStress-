#!/usr/bin/env python3
"""
NetStress 2.0 Power Trio - Performance Benchmark Comparison

Compares performance between:
1. Native Rust Engine (Power Trio)
2. Pure Python Fallback Engine

This benchmark measures real packet sending performance to localhost.
"""

import sys
import os
import time
import socket
import threading
import statistics
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.native_engine import (
    UltimateEngine, EngineConfig, Protocol, BackendType,
    get_capabilities, NATIVE_ENGINE_AVAILABLE
)


@dataclass
class BenchmarkResult:
    """Benchmark result data"""
    engine_type: str
    duration: float
    packets_sent: int
    bytes_sent: int
    pps: float
    mbps: float
    gbps: float
    errors: int
    
    def __str__(self):
        return f"""
{self.engine_type} Results:
  Duration:     {self.duration:.2f} seconds
  Packets Sent: {self.packets_sent:,}
  Bytes Sent:   {self.bytes_sent:,}
  Performance:  {self.pps:,.0f} PPS
  Bandwidth:    {self.mbps:.2f} Mbps ({self.gbps:.4f} Gbps)
  Errors:       {self.errors:,}
"""


class DummyUDPServer:
    """Simple UDP server to receive benchmark packets"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.packets_received = 0
        self.bytes_received = 0
        self._thread = None
    
    def start(self):
        """Start the dummy server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 64 * 1024 * 1024)
        except Exception:
            pass
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.1)
        self.running = True
        self.packets_received = 0
        self.bytes_received = 0
        
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        print(f"[Server] Listening on {self.host}:{self.port}")
    
    def _receive_loop(self):
        """Receive packets in a loop"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(65535)
                self.packets_received += 1
                self.bytes_received += len(data)
            except socket.timeout:
                continue
            except Exception:
                break
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.sock:
            self.sock.close()
        print(f"[Server] Received {self.packets_received:,} packets, {self.bytes_received:,} bytes")


def run_benchmark(
    engine_type: str,
    target: str,
    port: int,
    duration: int,
    threads: int,
    packet_size: int,
    rate_limit: int = 0
) -> BenchmarkResult:
    """Run a single benchmark test"""
    
    print(f"\n{'='*60}")
    print(f"Running {engine_type} Benchmark")
    print(f"{'='*60}")
    print(f"  Target:      {target}:{port}")
    print(f"  Duration:    {duration} seconds")
    print(f"  Threads:     {threads}")
    print(f"  Packet Size: {packet_size} bytes")
    print(f"  Rate Limit:  {'Unlimited' if rate_limit == 0 else f'{rate_limit:,} PPS'}")
    
    # Determine backend
    if engine_type == "Native (Rust)":
        backend = BackendType.NATIVE
    else:
        backend = BackendType.PYTHON
    
    # Create configuration
    config = EngineConfig(
        target=target,
        port=port,
        protocol=Protocol.UDP,
        threads=threads,
        packet_size=packet_size,
        rate_limit=rate_limit if rate_limit > 0 else None,
        backend=backend,
        duration=duration
    )
    
    try:
        # Create engine
        engine = UltimateEngine(config)
        
        print(f"  Backend:     {engine.backend_name}")
        print(f"\n  Starting benchmark...")
        
        # Run benchmark
        engine.start()
        
        # Monitor progress
        start_time = time.time()
        last_stats = None
        
        while time.time() - start_time < duration:
            time.sleep(1.0)
            stats = engine.get_stats()
            elapsed = time.time() - start_time
            print(f"  [{elapsed:5.1f}s] {stats.pps:>12,.0f} PPS | {stats.gbps:>8.4f} Gbps | {stats.packets_sent:>12,} packets")
            last_stats = stats
        
        # Stop and get final stats
        final_stats = engine.stop()
        
        return BenchmarkResult(
            engine_type=engine_type,
            duration=final_stats.duration,
            packets_sent=final_stats.packets_sent,
            bytes_sent=final_stats.bytes_sent,
            pps=final_stats.pps,
            mbps=final_stats.bps * 8 / 1_000_000,
            gbps=final_stats.gbps,
            errors=final_stats.errors
        )
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return BenchmarkResult(
            engine_type=engine_type,
            duration=0,
            packets_sent=0,
            bytes_sent=0,
            pps=0,
            mbps=0,
            gbps=0,
            errors=1
        )


def print_comparison(native_result: BenchmarkResult, python_result: BenchmarkResult):
    """Print comparison between native and Python results"""
    
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON: Native (Rust) vs Pure Python")
    print("="*70)
    
    print(native_result)
    print(python_result)
    
    # Calculate speedup
    if python_result.pps > 0:
        speedup = native_result.pps / python_result.pps
        print(f"\n{'='*70}")
        print(f"SPEEDUP: Native is {speedup:.2f}x faster than Pure Python")
        print(f"{'='*70}")
        
        print(f"\nDetailed Comparison:")
        print(f"  {'Metric':<20} {'Native':>15} {'Python':>15} {'Speedup':>12}")
        print(f"  {'-'*62}")
        print(f"  {'Packets/sec':<20} {native_result.pps:>15,.0f} {python_result.pps:>15,.0f} {speedup:>11.2f}x")
        print(f"  {'Bandwidth (Mbps)':<20} {native_result.mbps:>15,.2f} {python_result.mbps:>15,.2f} {native_result.mbps/max(1,python_result.mbps):>11.2f}x")
        print(f"  {'Total Packets':<20} {native_result.packets_sent:>15,} {python_result.packets_sent:>15,}")
        print(f"  {'Errors':<20} {native_result.errors:>15,} {python_result.errors:>15,}")
    else:
        print("\nCannot calculate speedup - Python benchmark failed or returned 0 PPS")


def main():
    """Main benchmark function"""
    
    print("\n" + "="*70)
    print("NetStress 2.0 Power Trio - Performance Benchmark")
    print("="*70)
    
    # Check capabilities
    caps = get_capabilities()
    print(f"\nSystem Capabilities:")
    print(f"  Platform:         {caps.platform}")
    print(f"  CPU Cores:        {caps.cpu_count}")
    print(f"  Native Available: {caps.native_available}")
    print(f"  Is Root/Admin:    {caps.is_root}")
    
    if not NATIVE_ENGINE_AVAILABLE:
        print("\n[WARNING] Native Rust engine not available!")
        print("Build it with: cd native/rust_engine && maturin develop --release")
    
    # Benchmark parameters
    TARGET = "127.0.0.1"
    PORT = 9999
    DURATION = 10  # seconds
    THREADS = 4
    PACKET_SIZE = 1472
    RATE_LIMIT = 0  # Unlimited
    
    # Start dummy server
    server = DummyUDPServer(TARGET, PORT)
    server.start()
    time.sleep(0.5)  # Let server start
    
    results = []
    
    try:
        # Run Native benchmark (if available)
        if NATIVE_ENGINE_AVAILABLE:
            native_result = run_benchmark(
                "Native (Rust)",
                TARGET, PORT, DURATION, THREADS, PACKET_SIZE, RATE_LIMIT
            )
            results.append(native_result)
            time.sleep(2)  # Cool down
        
        # Run Python benchmark
        python_result = run_benchmark(
            "Pure Python",
            TARGET, PORT, DURATION, THREADS, PACKET_SIZE, RATE_LIMIT
        )
        results.append(python_result)
        
    finally:
        server.stop()
    
    # Print comparison
    if len(results) == 2:
        print_comparison(results[0], results[1])
    elif len(results) == 1:
        print(results[0])
    
    # Save results
    print("\n" + "="*70)
    print("Benchmark Complete!")
    print("="*70)
    
    return results


if __name__ == "__main__":
    main()
