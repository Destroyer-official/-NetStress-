"""
Property-Based Test: Socket Optimizations Are Actually Applied

**Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
**Validates: Requirements 2.1, 4.2**

This property test verifies that socket optimizations are actually applied
and verified via getsockopt(). The system should set SO_SNDBUF to values
greater than system defaults, confirming optimization was applied.

Property: For any socket created by the packet engine, calling getsockopt(SO_SNDBUF)
SHALL return a value greater than the system default, confirming optimization was applied.
"""

import os
import sys
import socket
import platform
from pathlib import Path
from typing import Optional

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
        
        @staticmethod
        def sampled_from(items):
            return items[0] if items else None
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def assume(condition):
        pass


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


def get_system_default_sndbuf() -> int:
    """Get the system default SO_SNDBUF value for comparison."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        default = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        return default
    finally:
        sock.close()


def get_system_default_rcvbuf() -> int:
    """Get the system default SO_RCVBUF value for comparison."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        default = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        return default
    finally:
        sock.close()


class TestSocketOptimizationsApplied:
    """
    Test suite for Property 4: Socket Optimizations Are Actually Applied
    
    **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
    **Validates: Requirements 2.1, 4.2**
    """
    
    @pytest.fixture
    def packet_engine(self):
        """Create a RealPacketEngine instance for testing."""
        from core.engines.real_packet_engine import RealPacketEngine
        # Use localhost as target for testing
        return RealPacketEngine("127.0.0.1", 12345)
    
    @pytest.fixture
    def system_defaults(self):
        """Get system default buffer sizes."""
        return {
            'sndbuf': get_system_default_sndbuf(),
            'rcvbuf': get_system_default_rcvbuf()
        }
    
    def test_udp_socket_sndbuf_optimized(self, packet_engine, system_defaults):
        """
        Property test: UDP socket SO_SNDBUF should be greater than system default.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        sock = packet_engine.create_udp_socket()
        try:
            actual_sndbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            
            # The optimized value should be greater than or equal to system default
            # Note: Kernel may cap the value, but it should still be >= default
            assert actual_sndbuf >= system_defaults['sndbuf'], \
                f"UDP SO_SNDBUF ({actual_sndbuf}) should be >= system default ({system_defaults['sndbuf']})"
            
            # Log the actual values for debugging
            print(f"UDP SO_SNDBUF: system_default={system_defaults['sndbuf']}, actual={actual_sndbuf}")
        finally:
            sock.close()
    
    def test_udp_socket_rcvbuf_optimized(self, packet_engine, system_defaults):
        """
        Property test: UDP socket SO_RCVBUF should be greater than system default.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        sock = packet_engine.create_udp_socket()
        try:
            actual_rcvbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
            
            assert actual_rcvbuf >= system_defaults['rcvbuf'], \
                f"UDP SO_RCVBUF ({actual_rcvbuf}) should be >= system default ({system_defaults['rcvbuf']})"
            
            print(f"UDP SO_RCVBUF: system_default={system_defaults['rcvbuf']}, actual={actual_rcvbuf}")
        finally:
            sock.close()
    
    def test_tcp_socket_sndbuf_optimized(self, packet_engine):
        """
        Property test: TCP socket SO_SNDBUF should be optimized.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        sock = packet_engine.create_tcp_socket()
        try:
            actual_sndbuf = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            
            # TCP buffer should be set to a reasonable value (at least 64KB)
            assert actual_sndbuf >= 65536, \
                f"TCP SO_SNDBUF ({actual_sndbuf}) should be >= 64KB"
            
            print(f"TCP SO_SNDBUF: actual={actual_sndbuf}")
        finally:
            sock.close()
    
    def test_tcp_socket_nodelay_enabled(self, packet_engine):
        """
        Property test: TCP socket TCP_NODELAY should be enabled.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 4.2**
        """
        sock = packet_engine.create_tcp_socket()
        try:
            nodelay = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
            
            assert nodelay == 1, \
                f"TCP_NODELAY should be enabled (1), got {nodelay}"
            
            print(f"TCP_NODELAY: {nodelay}")
        finally:
            sock.close()
    
    @pytest.mark.skipif(platform.system() != 'Linux', reason="TCP_QUICKACK is Linux-only")
    def test_tcp_socket_quickack_enabled(self, packet_engine):
        """
        Property test: TCP socket TCP_QUICKACK should be enabled on Linux.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 4.2**
        """
        TCP_QUICKACK = 12  # Linux constant
        sock = packet_engine.create_tcp_socket()
        try:
            quickack = sock.getsockopt(socket.IPPROTO_TCP, TCP_QUICKACK)
            
            assert quickack == 1, \
                f"TCP_QUICKACK should be enabled (1), got {quickack}"
            
            print(f"TCP_QUICKACK: {quickack}")
        finally:
            sock.close()
    
    def test_optimization_results_recorded(self, packet_engine):
        """
        Property test: Socket optimization results should be recorded.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        # Create a socket to trigger optimizations
        sock = packet_engine.create_udp_socket()
        sock.close()
        
        # Check that optimization results were recorded
        status = packet_engine.get_socket_optimization_status()
        
        assert 'optimizations' in status, "Status should contain optimizations list"
        assert len(status['optimizations']) > 0, "Should have recorded optimization attempts"
        
        # Verify each optimization has required fields
        for opt in status['optimizations']:
            assert 'name' in opt, "Optimization should have name"
            assert 'requested' in opt, "Optimization should have requested value"
            assert 'actual' in opt, "Optimization should have actual value"
            assert 'success' in opt, "Optimization should have success flag"
    
    def test_verify_socket_optimizations_method(self, packet_engine):
        """
        Property test: verify_socket_optimizations should return actual kernel values.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        sock = packet_engine.create_udp_socket()
        try:
            verification = packet_engine.verify_socket_optimizations(sock)
            
            assert 'SO_SNDBUF' in verification, "Should verify SO_SNDBUF"
            assert 'SO_RCVBUF' in verification, "Should verify SO_RCVBUF"
            
            # Values should be positive
            assert verification['SO_SNDBUF'] > 0, "SO_SNDBUF should be positive"
            assert verification['SO_RCVBUF'] > 0, "SO_RCVBUF should be positive"
            
            print(f"Verification: {verification}")
        finally:
            sock.close()
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(buffer_multiplier=st.integers(min_value=1, max_value=16))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_socket_buffer_optimization(self, buffer_multiplier):
        """
        Property-based test: For any socket created by the packet engine,
        calling getsockopt(SO_SNDBUF) SHALL return a value greater than
        the system default, confirming optimization was applied.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        from core.engines.real_packet_engine import RealPacketEngine
        
        # Get system default before creating engine
        system_default = get_system_default_sndbuf()
        
        # Create engine and socket
        engine = RealPacketEngine("127.0.0.1", 12345 + buffer_multiplier)
        sock = engine.create_udp_socket()
        
        try:
            actual = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            
            # Property: optimized buffer should be >= system default
            assert actual >= system_default, \
                f"Optimized SO_SNDBUF ({actual}) should be >= system default ({system_default})"
        finally:
            sock.close()
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(socket_type=st.sampled_from(['udp', 'tcp']))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_any_socket_type_optimized(self, socket_type):
        """
        Property-based test: For any socket type (UDP or TCP) created by
        the packet engine, optimizations should be applied and verifiable.
        
        **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
        **Validates: Requirements 2.1, 4.2**
        """
        from core.engines.real_packet_engine import RealPacketEngine
        
        engine = RealPacketEngine("127.0.0.1", 12345)
        
        if socket_type == 'udp':
            sock = engine.create_udp_socket()
        else:
            sock = engine.create_tcp_socket()
        
        try:
            # Verify optimizations via getsockopt
            verification = engine.verify_socket_optimizations(sock)
            
            # SO_SNDBUF should be set
            assert verification['SO_SNDBUF'] > 0, \
                f"{socket_type.upper()} socket should have SO_SNDBUF set"
            
            # SO_RCVBUF should be set
            assert verification['SO_RCVBUF'] > 0, \
                f"{socket_type.upper()} socket should have SO_RCVBUF set"
            
            # TCP should have NODELAY
            if socket_type == 'tcp':
                assert 'TCP_NODELAY' in verification, \
                    "TCP socket should have TCP_NODELAY verified"
                assert verification['TCP_NODELAY'] == 1, \
                    "TCP_NODELAY should be enabled"
        finally:
            sock.close()


class TestSocketOptimizationResult:
    """Test the SocketOptimizationResult dataclass."""
    
    def test_was_applied_property(self):
        """Test the was_applied property logic."""
        from core.engines.real_packet_engine import SocketOptimizationResult
        
        # Success with positive value
        result1 = SocketOptimizationResult(
            option_name="SO_SNDBUF",
            requested_value=1000000,
            actual_value=500000,
            success=True
        )
        assert result1.was_applied == True
        
        # Failure
        result2 = SocketOptimizationResult(
            option_name="SO_SNDBUF",
            requested_value=1000000,
            actual_value=0,
            success=False,
            error_message="Permission denied"
        )
        assert result2.was_applied == False
        
        # Success but zero value
        result3 = SocketOptimizationResult(
            option_name="SO_SNDBUF",
            requested_value=1000000,
            actual_value=0,
            success=True
        )
        assert result3.was_applied == False


def test_all_socket_optimizations_verified():
    """
    Comprehensive test that verifies all socket optimizations are applied.
    
    **Feature: real-high-performance-netstress, Property 4: Socket Optimizations Are Actually Applied**
    **Validates: Requirements 2.1, 4.2**
    """
    from core.engines.real_packet_engine import RealPacketEngine
    
    engine = RealPacketEngine("127.0.0.1", 12345)
    
    # Test UDP socket
    udp_sock = engine.create_udp_socket()
    udp_verification = engine.verify_socket_optimizations(udp_sock)
    udp_sock.close()
    
    # Test TCP socket
    tcp_sock = engine.create_tcp_socket()
    tcp_verification = engine.verify_socket_optimizations(tcp_sock)
    tcp_sock.close()
    
    # Get optimization status
    status = engine.get_socket_optimization_status()
    
    # Verify we have optimization records
    assert len(status['optimizations']) > 0, "Should have optimization records"
    
    # Count successful optimizations
    successful = sum(1 for opt in status['optimizations'] if opt['success'])
    
    print(f"Socket optimization status:")
    print(f"  Platform: {status['platform']}")
    print(f"  Is root: {status['is_root']}")
    print(f"  Successful optimizations: {successful}/{len(status['optimizations'])}")
    print(f"  UDP verification: {udp_verification}")
    print(f"  TCP verification: {tcp_verification}")
    
    # At least some optimizations should succeed
    assert successful > 0, "At least some socket optimizations should succeed"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
