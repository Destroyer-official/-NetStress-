#!/usr/bin/env python3
"""
NetStress - Network Stress Testing Framework
Main Entry Point with Honest Capability Detection

This tool provides REAL network stress testing capabilities.
No simulations, no fake performance claims.
"""

import sys
import os
import platform
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check for required dependencies with honest error messages"""
    missing_deps = []
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")
    
    try:
        import scapy
    except ImportError:
        missing_deps.append("scapy")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True


def show_startup_banner():
    """Show honest startup banner with real capabilities"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    NetStress Framework                       ║
║              HONEST Network Stress Testing                   ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  FOR AUTHORIZED TESTING ONLY - USE RESPONSIBLY            ║
║                                                              ║
║  This tool provides REAL network stress testing:            ║
║  • Actual UDP/TCP packet generation                         ║
║  • Real socket optimizations                                ║
║  • Honest performance reporting                             ║
║  • No simulated features                                    ║
╚══════════════════════════════════════════════════════════════╝
    """)


def check_real_capabilities():
    """Check and report real capabilities"""
    try:
        # Try to import real components
        from core.capabilities.capability_report import CapabilityChecker
        
        checker = CapabilityChecker()
        caps = checker.get_full_report()
        
        print("🔍 CAPABILITY DETECTION:")
        print(f"   Platform: {caps.platform} {caps.platform_version}")
        print(f"   Python: {caps.python_version}")
        print(f"   Root/Admin: {'Yes' if caps.is_root else 'No'}")
        
        print("\n✅ AVAILABLE FEATURES:")
        if caps.udp_flood:
            print("   • UDP Flood (real packets)")
        if caps.tcp_flood:
            print("   • TCP Flood (real connections)")
        if caps.http_flood:
            print("   • HTTP Flood (real requests)")
        if caps.sendfile:
            print("   • sendfile() zero-copy")
        if caps.msg_zerocopy:
            print("   • MSG_ZEROCOPY (Linux 4.14+)")
        if caps.raw_sockets:
            print("   • Raw sockets (requires root)")
        
        print("\n❌ NOT IMPLEMENTED:")
        print("   • XDP (use xdp-tools)")
        print("   • eBPF (use bcc/libbpf)")
        print("   • DPDK (use dpdk.org)")
        print("   • Kernel bypass")
        
        print(f"\n📊 EXPECTED PERFORMANCE:")
        print(f"   • UDP: {caps.expected_udp_pps}")
        print(f"   • TCP: {caps.expected_tcp_cps}")
        print(f"   • Bandwidth: {caps.expected_bandwidth}")
        
        if caps.limitations:
            print("\n⚠️  LIMITATIONS:")
            for lim in caps.limitations[:3]:
                print(f"   • {lim}")
        
        return True
        
    except ImportError as e:
        logger.warning(f"Real capability detection not available: {e}")
        print("🔍 BASIC CAPABILITY DETECTION:")
        print(f"   Platform: {platform.system()} {platform.release()}")
        print(f"   Python: {platform.python_version()}")
        print(f"   Root/Admin: {'Yes' if os.geteuid() == 0 else 'No'}")
        
        print("\n✅ BASIC FEATURES AVAILABLE:")
        print("   • UDP Flood (socket.sendto)")
        print("   • TCP Flood (asyncio connections)")
        print("   • HTTP Flood (aiohttp)")
        
        print("\n❌ ADVANCED FEATURES:")
        print("   • Real performance monitoring: Not available")
        print("   • Zero-copy operations: Not available")
        print("   • Kernel optimizations: Not available")
        
        return False


def main():
    """Main entry point with honest capability detection"""
    
    # Show banner
    show_startup_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check real capabilities
    print("Detecting system capabilities...\n")
    has_real_caps = check_real_capabilities()
    
    print("\n" + "="*60)
    if has_real_caps:
        print("✅ REAL components loaded - using high-performance implementations")
    else:
        print("⚠️  Using basic implementations - install real components for better performance")
    print("="*60 + "\n")
    
    # Import and run main ddos module
    try:
        from ddos import main as ddos_main
        ddos_main()
    except ImportError as e:
        print(f"❌ Error importing ddos module: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
