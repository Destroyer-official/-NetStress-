#!/usr/bin/env python3
"""
NetStress Production CLI

Production-ready command-line interface for NetStress.
Supports all attack types, configuration, and reporting.
"""

import os
import sys
import time
import signal
import asyncio
import argparse
import platform
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ProductionConfig, ConfigManager, load_config
from core.logging_setup import setup_logging, get_logger

logger = get_logger(__name__)


# Version info
VERSION = "2.0.0"
CODENAME = "Power Trio"


def print_banner():
    """Print NetStress banner"""
    banner = f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ██╗███████╗████████╗███████╗████████╗██████╗ ███████╗███████╗███████╗║
║   ████╗  ██║██╔════╝╚══██╔══╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔════╝██╔════╝║
║   ██╔██╗ ██║█████╗     ██║   ███████╗   ██║   ██████╔╝█████╗  ███████╗███████╗║
║   ██║╚██╗██║██╔══╝     ██║   ╚════██║   ██║   ██╔══██╗██╔══╝  ╚════██║╚════██║║
║   ██║ ╚████║███████╗   ██║   ███████║   ██║   ██║  ██║███████╗███████║███████║║
║   ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝║
║                                                               ║
║   Version: {VERSION} ({CODENAME})                                    ║
║   Platform: {platform.system()} {platform.release()}                              ║
║                                                               ║
║   ⚠️  AUTHORIZED USE ONLY - FOR SECURITY TESTING              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def get_capabilities() -> Dict[str, Any]:
    """Get system capabilities"""
    caps = {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'native_engine': False,
        'dpdk': False,
        'af_xdp': False,
    }
    
    try:
        from core.native_engine import is_native_available, get_capabilities as native_caps
        caps['native_engine'] = is_native_available()
        if caps['native_engine']:
            caps.update(native_caps())
    except ImportError:
        pass
    
    return caps


async def run_health_check(verbose: bool = False) -> int:
    """Run comprehensive health check"""
    try:
        from core.health import check_health, HealthStatus
        
        print("\n=== Health Check ===\n")
        health = await check_health()
        
        # Status indicator
        status_colors = {
            HealthStatus.HEALTHY: '\033[92m',  # Green
            HealthStatus.DEGRADED: '\033[93m',  # Yellow
            HealthStatus.UNHEALTHY: '\033[91m',  # Red
            HealthStatus.UNKNOWN: '\033[94m',  # Blue
        }
        reset = '\033[0m'
        
        color = status_colors.get(health.status, '')
        print(f"Overall Status: {color}{health.status.value.upper()}{reset}")
        print(f"Version: {health.version}")
        print(f"Platform: {health.platform}")
        print(f"Uptime: {health.uptime_seconds:.1f}s")
        
        print("\n--- Component Checks ---\n")
        for check in health.checks:
            color = status_colors.get(check.status, '')
            symbol = {'healthy': '✓', 'degraded': '⚠', 'unhealthy': '✗', 'unknown': '?'}.get(check.status.value, '•')
            print(f"  {color}{symbol}{reset} {check.component}: {check.message}")
            if verbose and check.details:
                for key, value in check.details.items():
                    print(f"      {key}: {value}")
        
        print("\n--- Summary ---\n")
        summary = health.to_dict()['summary']
        print(f"  Total: {summary['total']}")
        print(f"  Healthy: {summary['healthy']}")
        print(f"  Degraded: {summary['degraded']}")
        print(f"  Unhealthy: {summary['unhealthy']}")
        
        return 0 if health.status == HealthStatus.HEALTHY else 1
        
    except ImportError as e:
        print(f"Health module not available: {e}")
        return 1
    except Exception as e:
        print(f"Health check failed: {e}")
        return 1


def print_status():
    """Print system status"""
    caps = get_capabilities()
    
    print("\n=== System Status ===\n")
    print(f"Platform: {caps['platform']}")
    print(f"Python: {caps['python_version']}")
    print(f"CPU Cores: {caps['cpu_count']}")
    print(f"Native Engine: {'✓ Available' if caps['native_engine'] else '✗ Not compiled'}")
    print(f"DPDK Support: {'✓ Available' if caps.get('dpdk') else '✗ Not available'}")
    print(f"AF_XDP Support: {'✓ Available' if caps.get('af_xdp') else '✗ Not available'}")
    
    # Performance estimates
    print("\n=== Performance Estimates ===\n")
    if caps['native_engine']:
        print("Mode: Native Rust Engine")
        print("UDP Throughput: 1M-10M+ PPS")
        print("TCP Connections: 50K-200K/sec")
    else:
        print("Mode: Pure Python")
        print("UDP Throughput: 50K-500K PPS")
        print("TCP Connections: 5K-50K/sec")
    
    print("\nTo build native engine:")
    print("  pip install maturin")
    print("  cd native/rust_engine")
    print("  maturin develop --release")


def validate_target(target: str, config: ProductionConfig) -> bool:
    """Validate target is allowed"""
    if not config.safety.enable_target_validation:
        return True
    
    # Check blocked targets
    blocked_file = config.safety.blocked_targets_file
    if os.path.exists(blocked_file):
        with open(blocked_file, 'r') as f:
            blocked = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if target in blocked:
                logger.error(f"Target {target} is blocked")
                return False
    
    # Basic validation
    import socket
    try:
        socket.gethostbyname(target)
        return True
    except socket.gaierror:
        logger.error(f"Cannot resolve target: {target}")
        return False


async def run_attack(args, config: ProductionConfig):
    """Run the attack"""
    from core.performance.ultra_engine import create_ultra_engine, EngineMode, UltraConfig
    
    # Validate target
    if not validate_target(args.target, config):
        return 1
    
    # Determine engine mode
    if args.native:
        mode = EngineMode.NATIVE
    elif args.python:
        mode = EngineMode.STANDARD
    else:
        mode = EngineMode.HYBRID
    
    # Create engine config
    engine_config = UltraConfig(
        target=args.target,
        port=args.port,
        mode=mode,
        threads=args.threads or config.performance.default_threads,
        packet_size=args.size or config.performance.default_packet_size,
        rate_limit=args.rate or 0,
        duration=args.duration,
        protocol=args.protocol.lower(),
    )
    
    logger.info(f"Starting attack on {args.target}:{args.port}")
    logger.info(f"Protocol: {args.protocol}, Duration: {args.duration}s")
    logger.info(f"Threads: {engine_config.threads}, Rate: {args.rate or 'unlimited'}")
    
    if config.dry_run:
        logger.info("DRY RUN - No packets will be sent")
        return 0
    
    # Create and run engine
    engine = create_ultra_engine(
        target=args.target,
        port=args.port,
        protocol=args.protocol.lower(),
        mode=mode,
        threads=engine_config.threads,
        packet_size=engine_config.packet_size,
        rate_limit=engine_config.rate_limit,
    )
    
    # Setup signal handler for graceful shutdown
    shutdown_requested = False
    
    def signal_handler(sig, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            logger.warning("Force shutdown...")
            sys.exit(1)
        shutdown_requested = True
        logger.info("Shutdown requested, stopping...")
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        engine.start()
        start_time = time.time()
        
        # Progress display
        while not shutdown_requested and (time.time() - start_time) < args.duration:
            stats = engine.get_stats()
            elapsed = time.time() - start_time
            remaining = args.duration - elapsed
            
            print(f"\r[{elapsed:.1f}s/{args.duration}s] "
                  f"PPS: {stats.pps:,.0f} | "
                  f"Mbps: {stats.mbps:.2f} | "
                  f"Packets: {stats.packets_sent:,} | "
                  f"Errors: {stats.errors:,}   ", end='', flush=True)
            
            await asyncio.sleep(0.5)
        
        print()  # New line after progress
        
    finally:
        engine.stop()
        final_stats = engine.get_stats()
        
        print("\n=== Attack Complete ===\n")
        print(f"Duration: {final_stats.duration:.2f} seconds")
        print(f"Packets Sent: {final_stats.packets_sent:,}")
        print(f"Bytes Sent: {final_stats.bytes_sent:,}")
        print(f"Average PPS: {final_stats.pps:,.0f}")
        print(f"Average Throughput: {final_stats.mbps:.2f} Mbps ({final_stats.gbps:.3f} Gbps)")
        print(f"Errors: {final_stats.errors:,}")
        
        # Save report if enabled
        if config.reporting.enable_reports:
            save_report(args, final_stats, config)
    
    return 0


def save_report(args, stats, config: ProductionConfig):
    """Save attack report"""
    import json
    from pathlib import Path
    
    report_dir = Path(config.reporting.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"attack_report_{timestamp}.json"
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'target': args.target,
        'port': args.port,
        'protocol': args.protocol,
        'duration_requested': args.duration,
        'duration_actual': stats.duration,
        'packets_sent': stats.packets_sent,
        'bytes_sent': stats.bytes_sent,
        'average_pps': stats.pps,
        'average_mbps': stats.mbps,
        'errors': stats.errors,
        'system': {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cpu_count': os.cpu_count(),
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {report_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NetStress - Network Stress Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -t 192.168.1.100 -p 80 -P UDP -d 60
  %(prog)s -t example.com -p 443 -P HTTPS -d 120 --threads 8
  %(prog)s --status
  %(prog)s --config config.json -t 192.168.1.100 -p 80

For more information, see: https://github.com/Destroyer-official/-NetStress-
        """
    )
    
    # Target options
    parser.add_argument('-t', '--target', help='Target IP or hostname')
    parser.add_argument('-p', '--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('-P', '--protocol', default='UDP',
                       choices=['UDP', 'TCP', 'HTTP', 'HTTPS', 'DNS', 'ICMP'],
                       help='Protocol (default: UDP)')
    
    # Attack options
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Duration in seconds (default: 60)')
    parser.add_argument('-r', '--rate', type=int, default=0,
                       help='Rate limit in PPS (0 = unlimited)')
    parser.add_argument('-s', '--size', type=int, default=1472,
                       help='Packet size in bytes (default: 1472)')
    parser.add_argument('-x', '--threads', type=int, default=0,
                       help='Number of threads (0 = auto)')
    
    # Engine options
    parser.add_argument('--native', action='store_true',
                       help='Force native Rust engine')
    parser.add_argument('--python', action='store_true',
                       help='Force pure Python engine')
    
    # Configuration
    parser.add_argument('-c', '--config', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run (no packets sent)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode (minimal output)')
    
    # Info commands
    parser.add_argument('--status', action='store_true',
                       help='Show system status')
    parser.add_argument('--health', action='store_true',
                       help='Run health check')
    parser.add_argument('--version', action='version',
                       version=f'NetStress {VERSION} ({CODENAME})')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if args.dry_run:
        config.dry_run = True
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else ('WARNING' if args.quiet else config.logging.level)
    setup_logging(
        level=log_level,
        log_file=config.logging.file_path,
        console_output=not args.quiet,
    )
    
    # Print banner unless quiet
    if not args.quiet:
        print_banner()
    
    # Handle info commands
    if args.status:
        print_status()
        return 0
    
    if args.health:
        return asyncio.run(run_health_check(args.verbose))

    
    # Validate required arguments
    if not args.target:
        parser.error("Target (-t/--target) is required")
    
    # Run attack
    try:
        return asyncio.run(run_attack(args, config))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
