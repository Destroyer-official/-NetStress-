#!/usr/bin/env python3
"""
Native Stats Bridge Demo

Demonstrates how the native stats bridge automatically feeds native engine
statistics to the Python analytics system.
"""

import asyncio
import time
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.native_engine import UltimateEngine, EngineConfig, Protocol
from core.analytics import (
    get_native_stats_bridge, 
    start_native_stats_collection,
    stop_native_stats_collection,
    get_metrics_collector
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_native_stats_integration():
    """Demonstrate native stats integration with analytics system"""
    
    print("=== Native Stats Bridge Demo ===\n")
    
    # Start the analytics system
    print("1. Starting analytics system...")
    metrics_collector = get_metrics_collector()
    await metrics_collector.start()
    
    # Start the native stats bridge
    await start_native_stats_collection()
    print("   ✓ Analytics system and stats bridge started\n")
    
    # Create a native engine (will use Python fallback if native not available)
    print("2. Creating native engine...")
    config = EngineConfig(
        target="127.0.0.1",  # Localhost for demo
        port=8080,
        protocol=Protocol.UDP,
        threads=2,
        packet_size=1472,
        rate_limit=1000,  # 1K PPS for demo
        duration=10
    )
    
    engine = UltimateEngine(config)
    print(f"   ✓ Engine created (native={engine._is_native})")
    print(f"   ✓ Backend: {engine.backend_name}\n")
    
    # Start the engine (this will automatically register with stats bridge)
    print("3. Starting packet generation...")
    engine.start()
    
    # Monitor stats for a few seconds
    print("4. Monitoring stats (native stats automatically fed to analytics)...")
    for i in range(5):
        await asyncio.sleep(1)
        
        # Get stats from engine
        engine_stats = engine.get_stats()
        
        # Get stats from analytics system
        analytics_summary = metrics_collector.get_metrics_summary(window_seconds=10)
        
        print(f"   Second {i+1}:")
        print(f"     Engine: {engine_stats.packets_sent:,} packets, "
              f"{engine_stats.pps:.0f} PPS, {engine_stats.mbps:.1f} Mbps")
        
        # Show analytics integration
        if 'attack' in analytics_summary.get('categories', {}):
            attack_metrics = analytics_summary['categories']['attack']
            if attack_metrics:
                print(f"     Analytics: Integrated ✓ ({len(attack_metrics)} metrics tracked)")
            else:
                print(f"     Analytics: No metrics yet")
        else:
            print(f"     Analytics: No attack metrics yet")
    
    print()
    
    # Stop the engine
    print("5. Stopping engine...")
    final_stats = engine.stop()
    print(f"   ✓ Final stats: {final_stats.packets_sent:,} packets sent")
    print(f"   ✓ Average: {final_stats.pps:.0f} PPS, {final_stats.mbps:.1f} Mbps\n")
    
    # Show final analytics summary
    print("6. Final analytics summary...")
    final_summary = metrics_collector.get_metrics_summary(window_seconds=30)
    
    print(f"   Collection stats:")
    print(f"     Total metrics: {final_summary['collection_stats']['total_metrics_collected']}")
    print(f"     Metrics/sec: {final_summary['collection_stats']['metrics_per_second']:.1f}")
    
    if 'attack' in final_summary.get('categories', {}):
        attack_metrics = final_summary['categories']['attack']
        print(f"   Attack metrics tracked: {len(attack_metrics)}")
        for metric_name, data in attack_metrics.items():
            if data.get('count', 0) > 0:
                print(f"     {metric_name}: avg={data.get('avg', 0):.1f}, "
                      f"max={data.get('max', 0):.1f}")
    
    # Show stats bridge info
    bridge = get_native_stats_bridge()
    bridge_stats = bridge.get_bridge_stats()
    print(f"\n   Stats bridge:")
    print(f"     Collections: {bridge_stats['total_collections']}")
    print(f"     Success rate: {bridge_stats['success_rate']:.1f}%")
    print(f"     Engines tracked: {bridge_stats['registered_engines']}")
    
    # Clean up
    print("\n7. Cleaning up...")
    await stop_native_stats_collection()
    await metrics_collector.stop()
    print("   ✓ Analytics system stopped\n")
    
    print("=== Demo Complete ===")
    print("\nKey Points:")
    print("• Native engines automatically register with the stats bridge")
    print("• Stats are fed to the existing Python analytics system")
    print("• No code changes needed in existing analytics consumers")
    print("• Works with both native Rust engines and Python fallbacks")


async def demo_multiple_engines():
    """Demonstrate multiple engines being tracked simultaneously"""
    
    print("\n=== Multiple Engines Demo ===\n")
    
    # Start analytics
    metrics_collector = get_metrics_collector()
    await metrics_collector.start()
    await start_native_stats_collection()
    
    # Create multiple engines
    engines = []
    for i in range(3):
        config = EngineConfig(
            target="127.0.0.1",
            port=8080 + i,
            protocol=Protocol.UDP,
            threads=1,
            rate_limit=500 + i * 100,  # Different rates
        )
        engine = UltimateEngine(config)
        engines.append(engine)
    
    print(f"Created {len(engines)} engines")
    
    # Start all engines
    for i, engine in enumerate(engines):
        engine.start()
        print(f"Started engine {i+1} (target port {8080+i})")
    
    # Monitor for a few seconds
    print("\nMonitoring multiple engines...")
    for second in range(3):
        await asyncio.sleep(1)
        total_pps = sum(engine.get_stats().pps for engine in engines)
        print(f"Second {second+1}: Combined {total_pps:.0f} PPS")
    
    # Stop all engines
    print("\nStopping engines...")
    for i, engine in enumerate(engines):
        stats = engine.stop()
        print(f"Engine {i+1}: {stats.packets_sent:,} packets")
    
    # Show bridge tracked all engines
    bridge = get_native_stats_bridge()
    bridge_stats = bridge.get_bridge_stats()
    print(f"\nStats bridge tracked {bridge_stats['registered_engines']} engines")
    print(f"Total collections: {bridge_stats['total_collections']}")
    
    # Clean up
    await stop_native_stats_collection()
    await metrics_collector.stop()
    
    print("Multiple engines demo complete!")


if __name__ == "__main__":
    print("NetStress Native Stats Bridge Demo")
    print("==================================")
    
    try:
        # Run main demo
        asyncio.run(demo_native_stats_integration())
        
        # Run multiple engines demo
        asyncio.run(demo_multiple_engines())
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()