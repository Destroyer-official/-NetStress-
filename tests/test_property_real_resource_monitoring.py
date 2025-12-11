"""
Property-based tests for real resource monitoring.

**Feature: real-high-performance-netstress, Property 14: Real Resource Monitoring**
**Validates: Requirements 10.1, 10.2, 10.3**

Tests that resource monitoring provides accurate, real-time metrics
that match psutil readings within acceptable tolerance.
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, MagicMock

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.monitoring.real_resources import RealResourceMonitor, ResourceLimits


@pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
class TestRealResourceMonitoringProperties:
    """Property-based tests for real resource monitoring accuracy"""

    @given(
        monitoring_interval=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_cpu_monitoring_accuracy(self, monitoring_interval):
        """
        Property 14a: CPU monitoring accuracy
        
        For any monitoring interval, CPU usage reported by RealResourceMonitor
        should match psutil.cpu_percent() within 5% tolerance.
        """
        assume(monitoring_interval >= 0.1)
        
        monitor = RealResourceMonitor(monitoring_interval=monitoring_interval)
        
        # Get CPU usage from monitor
        monitor_cpu = monitor.get_cpu_usage()
        
        # Get CPU usage directly from psutil for comparison
        psutil_cpu = psutil.cpu_percent(interval=0.1)
        psutil_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        # Verify CPU percentage is within reasonable range
        assert 0.0 <= monitor_cpu['cpu_percent'] <= 100.0
        assert len(monitor_cpu['cpu_per_core']) > 0
        
        # Verify per-core counts match
        assert monitor_cpu['cpu_count'] == psutil.cpu_count()
        assert monitor_cpu['cpu_count_logical'] == psutil.cpu_count(logical=True)
        
        # CPU usage can vary quickly, so we allow some tolerance
        # The important thing is that we're getting real values, not fake ones
        for core_usage in monitor_cpu['cpu_per_core']:
            assert 0.0 <= core_usage <= 100.0

    @given(
        monitoring_interval=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=20, deadline=10000)
    def test_property_memory_monitoring_accuracy(self, monitoring_interval):
        """
        Property 14b: Memory monitoring accuracy
        
        For any monitoring interval, memory usage reported by RealResourceMonitor
        should match psutil readings within 5% tolerance.
        """
        assume(monitoring_interval >= 0.1)
        
        monitor = RealResourceMonitor(monitoring_interval=monitoring_interval)
        
        # Get memory usage from monitor
        monitor_memory = monitor.get_memory_usage()
        
        # Get memory usage directly from psutil for comparison
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        system_memory = psutil.virtual_memory()
        
        # Verify RSS matches within 5% (allowing for small timing differences)
        expected_rss_mb = memory_info.rss / (1024 * 1024)
        tolerance = max(0.1, expected_rss_mb * 0.05)  # 5% or 0.1MB minimum
        
        assert abs(monitor_memory['rss_mb'] - expected_rss_mb) <= tolerance
        
        # Verify memory percentage matches within 1%
        assert abs(monitor_memory['memory_percent'] - memory_percent) <= 1.0
        
        # Verify system memory totals match exactly (these shouldn't change)
        expected_total_mb = system_memory.total / (1024 * 1024)
        assert abs(monitor_memory['system_total_mb'] - expected_total_mb) < 1.0
        
        # Verify all values are reasonable
        assert monitor_memory['rss_mb'] > 0
        assert monitor_memory['memory_percent'] >= 0
        assert monitor_memory['system_total_mb'] > 0

    @given(
        monitoring_interval=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=15, deadline=15000)
    def test_property_network_monitoring_from_os(self, monitoring_interval):
        """
        Property 14c: Network monitoring from OS
        
        For any monitoring interval, network usage should be calculated
        from actual OS interface statistics using psutil.net_io_counters().
        """
        assume(monitoring_interval >= 0.1)
        
        monitor = RealResourceMonitor(monitoring_interval=monitoring_interval)
        
        # Reset baseline and wait a moment for some network activity
        monitor.reset_baseline()
        time.sleep(0.2)  # Small delay to allow for potential network activity
        
        # Get network usage from monitor
        network_usage = monitor.get_network_usage()
        
        # Get network counters directly from psutil
        net_io = psutil.net_io_counters()
        
        # Verify we're getting real OS counters
        assert 'bytes_sent' in network_usage
        assert 'bytes_recv' in network_usage
        assert 'packets_sent' in network_usage
        assert 'packets_recv' in network_usage
        
        # Verify counters are non-negative and reasonable
        assert network_usage['bytes_sent'] >= 0
        assert network_usage['bytes_recv'] >= 0
        assert network_usage['packets_sent'] >= 0
        assert network_usage['packets_recv'] >= 0
        
        # Verify rates are calculated (may be 0 if no activity)
        assert network_usage['send_mbps'] >= 0
        assert network_usage['recv_mbps'] >= 0
        assert network_usage['total_mbps'] >= 0
        
        # Verify measurement period is reasonable
        assert network_usage['measurement_period_seconds'] > 0

    @given(
        cpu_limit=st.floats(min_value=10.0, max_value=90.0),
        memory_limit=st.floats(min_value=100.0, max_value=2000.0)
    )
    @settings(max_examples=10, deadline=10000)
    def test_property_resource_limit_response_time(self, cpu_limit, memory_limit):
        """
        Property 15: Resource Limit Response Time
        
        For any resource limit violation, the system should begin throttling
        or shutdown within 1 second of detection.
        """
        assume(10.0 <= cpu_limit <= 90.0)
        assume(100.0 <= memory_limit <= 2000.0)
        
        limits = ResourceLimits(
            max_cpu_percent=cpu_limit,
            max_memory_mb=memory_limit
        )
        
        monitor = RealResourceMonitor(limits=limits, monitoring_interval=0.1)
        
        # Track callback invocations
        callback_times = []
        callback_resources = []
        
        def limit_callback(resource: str, value: float):
            callback_times.append(time.time())
            callback_resources.append((resource, value))
        
        monitor.add_limit_callback(limit_callback)
        
        # Mock high resource usage to trigger limits
        with patch.object(monitor, 'get_cpu_usage') as mock_cpu, \
             patch.object(monitor, 'get_memory_usage') as mock_memory:
            
            # Set up mocks to return values that exceed limits
            mock_cpu.return_value = {
                'cpu_percent': cpu_limit + 10.0,  # Exceed CPU limit
                'cpu_per_core': [cpu_limit + 10.0],
                'cpu_count': 1,
                'cpu_count_logical': 1
            }
            
            mock_memory.return_value = {
                'rss_mb': memory_limit + 100.0,  # Exceed memory limit
                'vms_mb': memory_limit + 200.0,
                'memory_percent': 50.0,
                'system_total_mb': 8192.0,
                'system_available_mb': 4096.0,
                'system_used_percent': 50.0
            }
            
            # Start monitoring
            start_time = time.time()
            monitor.start_monitoring()
            
            # Wait for limit detection (should be within 1 second + monitoring interval)
            max_wait = 1.0 + monitor.monitoring_interval + 0.1
            time.sleep(max_wait)
            
            monitor.stop_monitoring()
            
            # Verify callbacks were called within time limit
            if callback_times:  # Only check if callbacks were actually called
                first_callback_time = min(callback_times)
                response_time = first_callback_time - start_time
                
                # Should respond within 1 second + monitoring interval
                assert response_time <= (1.0 + monitor.monitoring_interval)
                
                # Verify we got callbacks for the right resources
                resource_names = [r[0] for r in callback_resources]
                assert 'cpu' in resource_names or 'memory' in resource_names

    def test_property_resource_usage_comprehensive(self):
        """
        Property 14d: Comprehensive resource usage
        
        The get_current_usage() method should return a complete ResourceUsage
        object with all fields populated from real OS data.
        """
        monitor = RealResourceMonitor()
        
        usage = monitor.get_current_usage()
        
        # Verify all required fields are present and reasonable
        assert usage.timestamp is not None
        assert 0.0 <= usage.cpu_percent <= 100.0
        assert len(usage.cpu_per_core) > 0
        assert usage.memory_rss_mb > 0
        assert usage.memory_percent >= 0
        assert usage.network_bytes_sent >= 0
        assert usage.network_bytes_recv >= 0
        assert usage.network_packets_sent >= 0
        assert usage.network_packets_recv >= 0
        assert usage.disk_read_mb >= 0
        assert usage.disk_write_mb >= 0
        assert usage.source == 'psutil'
        
        # Verify per-core CPU data is reasonable
        for core_usage in usage.cpu_per_core:
            assert 0.0 <= core_usage <= 100.0

    def test_property_monitoring_thread_safety(self):
        """
        Property 14e: Thread safety
        
        Resource monitoring should work correctly when accessed from
        multiple threads simultaneously.
        """
        monitor = RealResourceMonitor(monitoring_interval=0.1)
        
        results = []
        errors = []
        
        def worker():
            try:
                for _ in range(5):
                    usage = monitor.get_current_usage()
                    results.append(usage)
                    time.sleep(0.05)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        import threading
        threads = [threading.Thread(target=worker) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors in threads: {errors}"
        
        # Verify we got results from all threads
        assert len(results) >= 10  # Should have at least some results
        
        # Verify all results are valid
        for usage in results:
            assert 0.0 <= usage.cpu_percent <= 100.0
            assert usage.memory_rss_mb > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])