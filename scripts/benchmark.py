#!/usr/bin/env python3
"""
NetStress 2.0 Benchmark Script

Runs performance benchmarks and generates reports.
"""

import os
import sys
import time
import json
import socket
import asyncio
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Result of a single benchmark"""
    name: str
    duration_seconds: float
    packets_sent: int
    bytes_sent: int
    pps: float
    mbps: float
    errors: int
    success: bool
    error_message: str = ""


@dataclass
class BenchmarkReport:
    """Complete benchmark report"""
    timestamp: str
    platform: str
    python_version: str
    cpu_count: int
    native_available: bool
    results: List[BenchmarkResult]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "platform": self.platform,
            "python_version": self.python_version,
            "cpu_count": self.cpu_count,
            "native_available": self.native_available,
            "results": [asdict(r) for r in self.results]
        }


def print_header(text: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_native_engine() -> bool:
    """Check if native engine is available"""
    try:
        from core.native_engine import is_native_available
        return is_native_available()
    except ImportError:
        return False


async def benchmark_socket_creation(iterations: int = 1000) -> BenchmarkResult:
    """Benchmark socket creation speed"""
    print("Running: Socket Creation Benchmark...")
    
    start = time.perf_counter()
    errors = 0
    
    for _ in range(iterations):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.close()
        except Exception:
            errors += 1
    
    duration = time.perf_counter() - start
    rate = iterations / duration
    
    result = BenchmarkResult(
        name="socket_creation",
        duration_seconds=duration,
        packets_sent=iterations,
        bytes_sent=0,
        pps=rate,
        mbps=0,
        errors=errors,
        success=errors == 0
    )
    
    print(f"  Sockets/sec: {rate:,.0f}")
    return result


async def benchmark_udp_localhost(
    duration: float = 5.0,
    packet_size: int = 1472
) -> BenchmarkResult:
    """Benchmark UDP sending to localhost"""
    print("Running: UDP Localhost Benchmark...")
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    
    # Create payload
    payload = b'X' * packet_size
    target = ("127.0.0.1", 9999)
    
    packets_sent = 0
    bytes_sent = 0
    errors = 0
    
    start = time.perf_counter()
    end_time = start + duration
    
    while time.perf_counter() < end_time:
        try:
            sock.sendto(payload, target)
            packets_sent += 1
            bytes_sent += packet_size
        except BlockingIOError:
            # Socket buffer full, continue
            pass
        except Exception:
            errors += 1
    
    actual_duration = time.perf_counter() - start
    sock.close()
    
    pps = packets_sent / actual_duration
    mbps = (bytes_sent * 8) / (actual_duration * 1_000_000)
    
    result = BenchmarkResult(
        name="udp_localhost",
        duration_seconds=actual_duration,
        packets_sent=packets_sent,
        bytes_sent=bytes_sent,
        pps=pps,
        mbps=mbps,
        errors=errors,
        success=True
    )
    
    print(f"  PPS: {pps:,.0f}")
    print(f"  Throughput: {mbps:.2f} Mbps")
    return result


async def benchmark_engine(duration: float = 5.0) -> BenchmarkResult:
    """Benchmark the packet engine"""
    print("Running: Packet Engine Benchmark...")
    
    try:
        from core.native_engine import NativePacketEngine, EngineConfig
        
        config = EngineConfig(
            target="127.0.0.1",
            port=9999,
            protocol="udp",
            threads=4,
            packet_size=1472
        )
        
        engine = NativePacketEngine(config)
        engine.start()
        
        await asyncio.sleep(duration)
        
        engine.stop()
        stats = engine.get_stats()
        
        result = BenchmarkResult(
            name="packet_engine",
            duration_seconds=stats.duration,
            packets_sent=stats.packets_sent,
            bytes_sent=stats.bytes_sent,
            pps=stats.pps,
            mbps=stats.mbps,
            errors=stats.errors,
            success=True
        )
        
        print(f"  PPS: {stats.pps:,.0f}")
        print(f"  Throughput: {stats.mbps:.2f} Mbps")
        return result
        
    except Exception as e:
        return BenchmarkResult(
            name="packet_engine",
            duration_seconds=0,
            packets_sent=0,
            bytes_sent=0,
            pps=0,
            mbps=0,
            errors=1,
            success=False,
            error_message=str(e)
        )


async def benchmark_async_connections(
    count: int = 100,
    timeout: float = 1.0
) -> BenchmarkResult:
    """Benchmark async connection creation"""
    print("Running: Async Connection Benchmark...")
    
    successful = 0
    errors = 0
    
    start = time.perf_counter()
    
    async def try_connect():
        nonlocal successful, errors
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", 80),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            successful += 1
        except Exception:
            errors += 1
    
    # Run connections concurrently
    tasks = [try_connect() for _ in range(count)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.perf_counter() - start
    rate = count / duration
    
    result = BenchmarkResult(
        name="async_connections",
        duration_seconds=duration,
        packets_sent=count,
        bytes_sent=0,
        pps=rate,
        mbps=0,
        errors=errors,
        success=True
    )
    
    print(f"  Connections/sec: {rate:,.0f}")
    print(f"  Successful: {successful}, Errors: {errors}")
    return result


async def run_benchmarks() -> BenchmarkReport:
    """Run all benchmarks"""
    print_header("NetStress 2.0 Benchmark Suite")
    
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"CPU Cores: {os.cpu_count()}")
    
    native = check_native_engine()
    print(f"Native Engine: {'Available' if native else 'Not Available'}")
    
    results = []
    
    # Run benchmarks
    results.append(await benchmark_socket_creation())
    results.append(await benchmark_udp_localhost())
    results.append(await benchmark_engine())
    results.append(await benchmark_async_connections())
    
    # Create report
    report = BenchmarkReport(
        timestamp=datetime.now().isoformat(),
        platform=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        cpu_count=os.cpu_count() or 1,
        native_available=native,
        results=results
    )
    
    return report


def print_summary(report: BenchmarkReport):
    """Print benchmark summary"""
    print_header("Benchmark Summary")
    
    for result in report.results:
        status = "✓" if result.success else "✗"
        print(f"{status} {result.name}:")
        print(f"    Duration: {result.duration_seconds:.2f}s")
        if result.pps > 0:
            print(f"    Rate: {result.pps:,.0f}/sec")
        if result.mbps > 0:
            print(f"    Throughput: {result.mbps:.2f} Mbps")
        if result.errors > 0:
            print(f"    Errors: {result.errors}")
        if result.error_message:
            print(f"    Error: {result.error_message}")
        print()


def save_report(report: BenchmarkReport, output_dir: str = "benchmark_reports"):
    """Save benchmark report to file"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/benchmark_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"Report saved to: {filename}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NetStress Benchmark Suite")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--output", default="benchmark_reports", help="Output directory")
    args = parser.parse_args()
    
    report = await run_benchmarks()
    print_summary(report)
    
    if args.save:
        save_report(report, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
