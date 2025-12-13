#!/usr/bin/env python3
"""
NetStress Performance Benchmark: Native Rust vs Pure Python
============================================================
Compares packet generation performance between:
- Native Rust engine (with IOCP on Windows, io_uring on Linux)
- Pure Python fallback engine

This benchmark sends UDP packets to localhost to measure raw performance
without network bottlenecks.
"""

import sys
import os
import time
import socket
import threading
import statistics

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.native_engine import (
    UltimateEngine, EngineConfig, Protocol, BackendType,
    PythonFallbackEngine, get_capabilities, NATIVE_ENGINE_AVAILABLE
)


class BenchmarkResults:
    """Store and display benchmark results"""
    def __init__(self, name: str):
        self.name = name
        self.packets_sent = 0
        self.bytes_sent = 0
        self.duration = 0.0
        self.pps = 0.0
        self.mbps = 0.0
        self.errors = 0
    
    def __str__(self):
        return (
            f"{self.name}:\n"
            f"  Packets Sent: {self.packets_sent:,}\n"
            f"  Bytes Sent: {self.bytes_sent:,}\n"
            f"  Duration: {self.duration:.2f}s\n"
            f"  PPS: {self.pps:,.0f}\n"
            f"  Throughput: {self.mbps:.2f} Mbps\n"
            f"  Errors: {self.errors}"
        )


def create_udp_sink(port: int) -> tuple:
    """Create a UDP socket to receive packets (sink)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)
    sock.bind(('127.0.0.1', port))
    sock.setblocking(False)
    return sock


def benchmark_native_engine(duration: int, port: int, threads: int, packet_size: int) -> BenchmarkResults:
    """Benchmark the native Rust engine"""
    results = BenchmarkResults("Native Rust Engine")
    
    if not NATIVE_ENGINE_AVAILABLE:
        print("  [SKIP] Native engine not available")
        return results
    
    config = EngineConfig(
        target='127.0.0.1',
        port=port,
        protocol=Protocol.UDP,
        threads=threads,
        packet_size=packet_size,
        backend=BackendType.NATIVE,
        rate_limit=0,  # Unlimited
    )
    
    try:
        engine = UltimateEngine(config)
        
        print(f"  Starting native engine ({threads} threads, {packet_size} byte packets)...")
        engine.start()
        time.sleep(duration)
        stats = engine.stop()
        
        results.packets_sent = stats.packets_sent
        results.bytes_sent = stats.bytes_sent
        results.duration = stats.duration
        results.pps = stats.pps
        results.mbps = stats.bps * 8 / 1_000_000
        results.errors = stats.errors
        
    except Exception as e:
        print(f"  [ERROR] Native engine failed: {e}")
        results.errors = 1
    
    return results


def benchmark_python_engine(duration: int, port: int, threads: int, packet_size: int) -> BenchmarkResults:
    """Benchmark the pure Python fallback engine"""
    results = BenchmarkResults("Pure Python Engine")
    
    config = EngineConfig(
        target='127.0.0.1',
        port=port,
        protocol=Protocol.UDP,
        threads=threads,
        packet_size=packet_size,
        backend=BackendType.PYTHON,
        rate_limit=0,  # Unlimited
    )
    
    try:
        engine = PythonFallbackEngine(config)
        
        print(f"  Starting Python engine ({threads} threads, {packet_size} byte packets)...")
        engine.start()
        time.sleep(duration)
        engine.stop()
        stats = engine.get_stats()
        
        results.packets_sent = stats.get('packets_sent', 0)
        results.bytes_sent = stats.get('bytes_sent', 0)
        results.duration = stats.get('duration_secs', duration)
        results.pps = stats.get('packets_per_second', 0)
        results.mbps = stats.get('bytes_per_second', 0) * 8 / 1_000_000
        results.errors = stats.get('errors', 0)
        
    except Exception as e:
        print(f"  [ERROR] Python engine failed: {e}")
        results.errors = 1
    
    return results


def print_comparison(native: BenchmarkResults, python: BenchmarkResults):
    """Print comparison between native and Python results"""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    print(f"\n{native}\n")
    print(f"{python}\n")
    
    if python.pps > 0 and native.pps > 0:
        speedup = native.pps / python.pps
        print("-" * 60)
        print(f"SPEEDUP: Native is {speedup:.1f}x faster than Python")
        print(f"  Native PPS:  {native.pps:>12,.0f}")
        print(f"  Python PPS:  {python.pps:>12,.0f}")
        print(f"  Difference:  {native.pps - python.pps:>12,.0f} PPS")
        print("-" * 60)
    elif native.pps > 0:
        print("-" * 60)
        print(f"Native engine achieved {native.pps:,.0f} PPS")
        print("Python engine did not produce results for comparison")
        print("-" * 60)


def print_system_info():
    """Print system capabilities"""
    caps = get_capabilities()
    
    print("\n" + "=" * 60)
    print("SYSTEM CAPABILITIES")
    print("=" * 60)
    print(f"Platform: {caps.platform}")
    print(f"Architecture: {caps.arch}")
    print(f"CPU Cores: {caps.cpu_count}")
    print(f"Admin/Root: {caps.is_root}")
    print(f"Native Engine: {'Available' if NATIVE_ENGINE_AVAILABLE else 'Not Available'}")
    
    if caps.platform == "Windows":
        print(f"\nWindows Features:")
        print(f"  IOCP: {caps.has_iocp}")
        print(f"  Registered I/O: {caps.has_registered_io}")
    elif caps.platform == "Linux":
        print(f"\nLinux Features:")
        print(f"  sendmmsg: {caps.has_sendmmsg}")
        print(f"  io_uring: {caps.has_io_uring}")
        print(f"  AF_XDP: {caps.has_af_xdp}")
    elif caps.platform == "Darwin":
        print(f"\nmacOS Features:")
        print(f"  kqueue: {caps.has_kqueue}")
    
    print(f"\nCommon Features:")
    print(f"  Raw Socket: {caps.has_raw_socket}")
    print(f"  DPDK: {caps.has_dpdk}")
    print("=" * 60)


def main():
    """Run the benchmark"""
    print("\n" + "=" * 60)
    print("NetStress Performance Benchmark")
    print("Native Rust Engine vs Pure Python Engine")
    print("=" * 60)
    
    # Configuration
    DURATION = 5  # seconds per test
    PORT = 19999
    THREADS = 4
    PACKET_SIZE = 64  # Small packets for max PPS
    
    print_system_info()
    
    # Create UDP sink to receive packets
    print(f"\nCreating UDP sink on port {PORT}...")
    try:
        sink = create_udp_sink(PORT)
        print("  UDP sink ready")
    except Exception as e:
        print(f"  Warning: Could not create sink: {e}")
        sink = None
    
    print(f"\nBenchmark Configuration:")
    print(f"  Duration: {DURATION} seconds per test")
    print(f"  Threads: {THREADS}")
    print(f"  Packet Size: {PACKET_SIZE} bytes")
    print(f"  Target: 127.0.0.1:{PORT}")
    
    # Run benchmarks
    print("\n" + "-" * 60)
    print("Running Native Rust Engine Benchmark...")
    print("-" * 60)
    native_results = benchmark_native_engine(DURATION, PORT, THREADS, PACKET_SIZE)
    
    # Brief pause between tests
    time.sleep(1)
    
    print("\n" + "-" * 60)
    print("Running Pure Python Engine Benchmark...")
    print("-" * 60)
    python_results = benchmark_python_engine(DURATION, PORT, THREADS, PACKET_SIZE)
    
    # Print comparison
    print_comparison(native_results, python_results)
    
    # Cleanup
    if sink:
        sink.close()
    
    print("\nBenchmark complete!")
    
    return native_results, python_results


if __name__ == "__main__":
    main()
