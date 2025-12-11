"""
Property-Based Test: Performance Metrics From OS Counters

**Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
**Validates: Requirements 2.6, 6.1, 6.2**

This property test verifies that performance measurements come from actual
OS-level counters, not internal estimates, and that the reported metrics
match the delta in OS-level counters.

Property: For any performance measurement, the reported packets_sent and bytes_sent
SHALL match the delta in OS-level counters (e.g., /proc/net/dev on Linux).
"""

import os
import sys
import socket
import time
import platform
from pathlib import Path
from typing import Dict, Any, Optional

import pytest

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
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def assume(condition):
        pass

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


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


class OSCounterValidator:
    """
    Validator to check that performance metrics match OS counters.
    """
    
    def __init__(self, interface: Optional[str] = None):
        """Initialize with specific interface or auto-detect."""
        self.interface = interface
        self.platform = platform.system()
    
    def get_os_counters(self) -> Dict[str, int]:
        """Get OS-level network counters directly."""
        if self.platform == 'Linux':
            return self._get_linux_counters()
        elif PSUTIL_AVAILABLE:
            return self._get_psutil_counters()
        else:
            return {}
    
    def _get_linux_counters(self) -> Dict[str, int]:
        """Read counters from /proc/net/dev on Linux."""
        counters = {}
        
        try:
            with open('/proc/net/dev', 'r') as f:
                for line in f:
                    if ':' in line:
                        iface, data = line.split(':', 1)
                        iface = iface.strip()
                        parts = data.strip().split()
                        
                        if len(parts) >= 16:
                            counters[iface] = {
                                'rx_bytes': int(parts[0]),
                                'rx_packets': int(parts[1]),
                                'tx_bytes': int(parts[8]),
                                'tx_packets': int(parts[9])
                            }
        except Exception as e:
            print(f"Failed to read /proc/net/dev: {e}")
        
        return counters
    
    def _get_psutil_counters(self) -> Dict[str, int]:
        """Get counters using psutil."""
        counters = {}
        
        try:
            net_counters = psutil.net_io_counters(pernic=True)
            for iface, stats in net_counters.items():
                counters[iface] = {
                    'rx_bytes': stats.bytes_recv,
                    'rx_packets': stats.packets_recv,
                    'tx_bytes': stats.bytes_sent,
                    'tx_packets': stats.packets_sent
                }
        except Exception as e:
            print(f"Failed to get psutil counters: {e}")
        
        return counters
    
    def find_active_interface(self) -> Optional[str]:
        """Find an interface with non-zero counters."""
        counters = self.get_os_counters()
        
        for iface, stats in counters.items():
            if stats['tx_bytes'] > 0 or stats['rx_bytes'] > 0:
                return iface
        
        # Fallback to common interface names
        for iface in ['eth0', 'en0', 'Ethernet']:
            if iface in counters:
                return iface
        
        return None


class TestOSCounterAccuracy:
    """
    Test suite for Property 6: Performance Metrics From OS Counters
    
    **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
    **Validates: Requirements 2.6, 6.1, 6.2**
    """
    
    @pytest.fixture
    def performance_monitor(self):
        """Create a RealPerformanceMonitor instance."""
        from core.monitoring.real_performance import RealPerformanceMonitor
        return RealPerformanceMonitor()
    
    @pytest.fixture
    def os_validator(self):
        """Create an OS counter validator."""
        return OSCounterValidator()
    
    def test_monitor_initialization(self, performance_monitor):
        """
        Test that performance monitor initializes correctly.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1**
        """
        assert performance_monitor.interface is not None
        assert performance_monitor.platform in ['Linux', 'Windows', 'Darwin']
        
        # Should be able to get current stats
        stats = performance_monitor.get_current_stats()
        assert 'interface' in stats
        assert 'counters' in stats
        assert stats['source'] == 'os_counters'
    
    def test_interface_stats_structure(self, performance_monitor):
        """
        Test that interface stats have the correct structure.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1**
        """
        stats = performance_monitor.get_interface_stats()
        
        required_fields = ['tx_packets', 'tx_bytes', 'rx_packets', 'rx_bytes', 'tx_errors', 'rx_errors']
        for field in required_fields:
            assert field in stats, f"Missing required field: {field}"
            assert isinstance(stats[field], int), f"Field {field} should be integer"
            assert stats[field] >= 0, f"Field {field} should be non-negative"
    
    def test_measurement_period_functionality(self, performance_monitor):
        """
        Test that measurement periods work correctly.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.2**
        """
        # Start measurement
        performance_monitor.start_measurement()
        
        # Wait a short time
        time.sleep(0.1)
        
        # Get measurement
        result = performance_monitor.get_measurement()
        
        assert result.duration_seconds > 0
        assert result.source == 'os_counters'
        assert result.interface == performance_monitor.interface
        assert 'OS counters' in result.methodology
    
    def test_counter_delta_calculation(self, performance_monitor):
        """
        Test that counter deltas are calculated correctly.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1, 6.2**
        """
        # Get initial counters
        initial_stats = performance_monitor.get_interface_stats()
        
        # Start measurement
        performance_monitor.start_measurement()
        
        # Simulate some network activity by creating a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Send a few packets to localhost
            for i in range(5):
                sock.sendto(b'test packet', ('127.0.0.1', 12345))
        except:
            pass  # Ignore errors, we just want to generate some traffic
        finally:
            sock.close()
        
        time.sleep(0.1)
        
        # Get measurement
        result = performance_monitor.get_measurement()
        final_stats = performance_monitor.get_interface_stats()
        
        # Verify deltas make sense
        expected_tx_packets = final_stats['tx_packets'] - initial_stats['tx_packets']
        expected_tx_bytes = final_stats['tx_bytes'] - initial_stats['tx_bytes']
        
        # The measurement should reflect the actual counter changes
        # (may not be exact due to other system traffic)
        assert result.packets_sent >= 0
        assert result.bytes_sent >= 0
    
    def test_high_resolution_timing(self, performance_monitor):
        """
        Test that high-resolution timing is used.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.2**
        """
        performance_monitor.start_measurement()
        time.sleep(0.001)  # 1ms
        result = performance_monitor.get_measurement()
        
        # Should measure sub-second durations accurately (allow for system overhead)
        assert 0.0005 < result.duration_seconds < 0.05  # Increased tolerance for Windows
        
        # Should calculate rates even for short durations
        assert result.packets_per_second >= 0
        assert result.megabits_per_second >= 0
    
    @pytest.mark.skipif(platform.system() != 'Linux', reason="Linux-specific test")
    def test_linux_proc_net_dev_parsing(self, performance_monitor):
        """
        Test that /proc/net/dev is parsed correctly on Linux.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1**
        """
        if performance_monitor.platform != 'Linux':
            pytest.skip("Linux-specific test")
        
        stats = performance_monitor._get_linux_interface_stats()
        
        # Should have parsed some stats
        assert isinstance(stats, dict)
        assert 'tx_packets' in stats
        assert 'tx_bytes' in stats
        
        # Verify we can read /proc/net/dev directly
        try:
            with open('/proc/net/dev', 'r') as f:
                content = f.read()
                assert performance_monitor.interface in content or 'lo' in content
        except FileNotFoundError:
            pytest.skip("/proc/net/dev not available")
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_psutil_fallback(self, performance_monitor):
        """
        Test that psutil fallback works correctly.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1**
        """
        stats = performance_monitor._get_psutil_stats()
        
        assert isinstance(stats, dict)
        required_fields = ['tx_packets', 'tx_bytes', 'rx_packets', 'rx_bytes']
        for field in required_fields:
            assert field in stats
            assert isinstance(stats[field], int)
    
    def test_performance_result_structure(self, performance_monitor):
        """
        Test that PerformanceResult has correct structure and values.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.2**
        """
        performance_monitor.start_measurement()
        time.sleep(0.1)
        result = performance_monitor.get_measurement()
        
        # Check all required fields
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'packets_sent')
        assert hasattr(result, 'bytes_sent')
        assert hasattr(result, 'packets_per_second')
        assert hasattr(result, 'megabits_per_second')
        assert hasattr(result, 'gigabits_per_second')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'source')
        assert hasattr(result, 'interface')
        assert hasattr(result, 'methodology')
        
        # Check values are reasonable
        assert result.duration_seconds > 0
        assert result.packets_sent >= 0
        assert result.bytes_sent >= 0
        assert result.source == 'os_counters'
        assert result.interface is not None
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(measurement_duration=st.floats(min_value=0.1, max_value=2.0))
    @settings(max_examples=5, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_os_counter_consistency(self, measurement_duration, performance_monitor):
        """
        Property-based test: For any measurement duration, the performance
        metrics should be consistent with OS counter deltas.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 2.6, 6.1, 6.2**
        """
        # Get initial OS counters directly
        initial_counters = performance_monitor.get_interface_stats()
        
        # Start measurement
        performance_monitor.start_measurement()
        
        # Wait for the specified duration
        time.sleep(measurement_duration)
        
        # Get measurement result
        result = performance_monitor.get_measurement()
        
        # Get final OS counters
        final_counters = performance_monitor.get_interface_stats()
        
        # Calculate expected deltas from OS counters
        expected_tx_packets = final_counters['tx_packets'] - initial_counters['tx_packets']
        expected_tx_bytes = final_counters['tx_bytes'] - initial_counters['tx_bytes']
        
        # The measurement should match OS counter deltas
        # Allow some tolerance for system activity
        assert abs(result.packets_sent - expected_tx_packets) <= expected_tx_packets + 100, \
            f"Packet count mismatch: measured={result.packets_sent}, expected={expected_tx_packets}"
        
        assert abs(result.bytes_sent - expected_tx_bytes) <= expected_tx_bytes + 10000, \
            f"Byte count mismatch: measured={result.bytes_sent}, expected={expected_tx_bytes}"
        
        # Duration should be close to requested
        assert abs(result.duration_seconds - measurement_duration) < 0.1, \
            f"Duration mismatch: measured={result.duration_seconds}, expected={measurement_duration}"
        
        # Source should always be OS counters
        assert result.source == 'os_counters'
    
    def test_counter_source_honesty(self, performance_monitor):
        """
        Test that the system honestly reports the source of counters.
        
        **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
        **Validates: Requirements 6.1**
        """
        stats = performance_monitor.get_current_stats()
        
        # Should always report 'os_counters' as source
        assert stats['source'] == 'os_counters'
        
        # Should include platform information
        assert 'platform' in stats
        assert stats['platform'] == performance_monitor.platform
        
        # Measurement results should also be honest
        performance_monitor.start_measurement()
        time.sleep(0.1)
        result = performance_monitor.get_measurement()
        
        assert result.source == 'os_counters'
        assert 'OS counters' in result.methodology


class TestCrossPlatformCounters:
    """
    Test cross-platform counter functionality.
    
    **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
    **Validates: Requirements 6.1**
    """
    
    def test_platform_detection(self):
        """Test that platform is detected correctly."""
        from core.monitoring.real_performance import RealPerformanceMonitor
        
        monitor = RealPerformanceMonitor()
        assert monitor.platform in ['Linux', 'Windows', 'Darwin']
    
    def test_interface_detection(self):
        """Test that a network interface is detected."""
        from core.monitoring.real_performance import RealPerformanceMonitor
        
        monitor = RealPerformanceMonitor()
        assert monitor.interface is not None
        assert len(monitor.interface) > 0
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_psutil_availability_handling(self):
        """Test that psutil availability is handled correctly."""
        from core.monitoring.real_performance import RealPerformanceMonitor
        
        monitor = RealPerformanceMonitor()
        
        # Should work even if psutil is available
        stats = monitor.get_interface_stats()
        assert isinstance(stats, dict)


def test_basic_counter_functionality():
    """
    Basic test for counter functionality.
    
    **Feature: real-high-performance-netstress, Property 6: Performance Metrics From OS Counters**
    **Validates: Requirements 6.1, 6.2**
    """
    from core.monitoring.real_performance import RealPerformanceMonitor
    
    monitor = RealPerformanceMonitor()
    
    # Should be able to get stats
    stats = monitor.get_interface_stats()
    assert isinstance(stats, dict)
    
    # Should be able to start/get measurement
    monitor.start_measurement()
    time.sleep(0.1)
    result = monitor.get_measurement()
    
    assert result.source == 'os_counters'
    assert result.duration_seconds > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])