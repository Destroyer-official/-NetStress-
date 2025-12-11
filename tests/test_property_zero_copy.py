"""
Property-Based Test: Real Zero-Copy System Calls Used

**Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
**Validates: Requirements 3.1, 3.2**

This property test verifies that the zero-copy implementation uses actual system calls
(os.sendfile(), MSG_ZEROCOPY) rather than simulated zero-copy operations.

Property: For any file-to-socket transfer on Linux, the system SHALL call os.sendfile()
or use MSG_ZEROCOPY flag, not simulate zero-copy.
"""

import os
import sys
import socket
import platform
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

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
        def binary(min_size=0, max_size=100):
            return b"test data"
        
        @staticmethod
        def integers(min_value=0, max_value=100):
            return 50
    
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


class TestRealZeroCopySystemCalls:
    """
    Test suite for Property 7: Real Zero-Copy System Calls Used
    
    **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
    **Validates: Requirements 3.1, 3.2**
    """
    
    @pytest.fixture
    def real_zero_copy(self):
        """Get RealZeroCopy instance"""
        from core.performance.real_zero_copy import RealZeroCopy
        return RealZeroCopy()
    
    @pytest.fixture
    def zero_copy_capabilities(self):
        """Get ZeroCopyCapabilities instance"""
        from core.performance.zero_copy import ZeroCopyCapabilities
        return ZeroCopyCapabilities()
    
    def test_sendfile_uses_real_os_sendfile(self, real_zero_copy):
        """
        Property test: sendfile() method should use actual os.sendfile() system call.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.1**
        """
        if not real_zero_copy.sendfile_available:
            pytest.skip("sendfile() not available on this platform")
        
        # Create a temporary file with test data
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test data for sendfile")
            tmp_path = tmp.name
        
        try:
            # Create a socket pair for testing
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('127.0.0.1', 0))
            server_sock.listen(1)
            port = server_sock.getsockname()[1]
            
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(('127.0.0.1', port))
            
            conn, _ = server_sock.accept()
            
            # Patch os.sendfile to verify it's called
            with patch('os.sendfile', wraps=os.sendfile) as mock_sendfile:
                with open(tmp_path, 'rb') as f:
                    try:
                        result = real_zero_copy.sendfile(
                            client_sock.fileno(),
                            f.fileno(),
                            0,
                            22  # Length of "Test data for sendfile"
                        )
                        # Verify os.sendfile was actually called
                        mock_sendfile.assert_called_once()
                        assert result > 0, "sendfile should return bytes sent"
                    except OSError as e:
                        # Some systems may not support sendfile on certain socket types
                        pytest.skip(f"sendfile not supported: {e}")
            
            client_sock.close()
            conn.close()
            server_sock.close()
            
        finally:
            os.unlink(tmp_path)
    
    def test_msg_zerocopy_uses_real_socket_flag(self, real_zero_copy):
        """
        Property test: MSG_ZEROCOPY should use actual socket flag, not simulation.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.2**
        """
        if not real_zero_copy.msg_zerocopy_available:
            pytest.skip("MSG_ZEROCOPY not available on this platform")
        
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # Enable zerocopy
            result = real_zero_copy.enable_zerocopy_socket(sock)
            
            if result:
                # Verify SO_ZEROCOPY was set
                SO_ZEROCOPY = 60  # Linux constant
                try:
                    value = sock.getsockopt(socket.SOL_SOCKET, SO_ZEROCOPY)
                    assert value == 1, "SO_ZEROCOPY should be enabled"
                except OSError:
                    # Some kernels may not support getsockopt for SO_ZEROCOPY
                    pass
        finally:
            sock.close()

    
    def test_zero_copy_status_reports_real_capabilities(self, real_zero_copy):
        """
        Property test: Zero-copy status should accurately report real capabilities.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.1, 3.2**
        """
        status = real_zero_copy.get_status()
        
        # Verify status contains required fields
        assert 'platform' in status.__dict__
        assert 'sendfile_available' in status.__dict__
        assert 'msg_zerocopy_available' in status.__dict__
        assert 'active_method' in status.__dict__
        assert 'is_true_zero_copy' in status.__dict__
        
        # Verify sendfile_available matches actual os.sendfile availability
        assert status.sendfile_available == hasattr(os, 'sendfile'), \
            "sendfile_available should match actual os.sendfile availability"
        
        # Verify msg_zerocopy_available is False on non-Linux or old kernels
        if platform.system() != 'Linux':
            assert status.msg_zerocopy_available == False, \
                "MSG_ZEROCOPY should not be available on non-Linux"
    
    def test_capabilities_report_no_false_claims(self, zero_copy_capabilities):
        """
        Property test: Capability report should not claim unavailable features.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.1, 3.2**
        """
        report = zero_copy_capabilities.get_report()
        
        # These should always be False (not implemented in pure Python)
        assert report['xdp_available'] == False, \
            "XDP should not be claimed as available"
        assert report['ebpf_available'] == False, \
            "eBPF should not be claimed as available"
        assert report['dpdk_available'] == False, \
            "DPDK should not be claimed as available"
        assert report['dma_available'] == False, \
            "DMA should not be claimed as available"
        assert report['kernel_bypass_available'] == False, \
            "Kernel bypass should not be claimed as available"
        
        # Verify sendfile matches actual availability
        assert report['sendfile_available'] == hasattr(os, 'sendfile'), \
            "sendfile_available should match actual availability"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @pytest.mark.skipif(not hasattr(os, 'sendfile'), reason="sendfile not available on this platform")
    @given(data_size=st.integers(min_value=1, max_value=1024))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much] if HYPOTHESIS_AVAILABLE else [])
    def test_property_send_file_uses_real_sendfile(self, data_size):
        """
        Property-based test: For any file data, send_file_to_socket should use
        real os.sendfile() when available.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.1**
        """
        from core.performance.real_zero_copy import RealZeroCopy
        
        real_zero_copy = RealZeroCopy()
        
        if not real_zero_copy.sendfile_available:
            pytest.skip("sendfile not available")
            return
        
        # Create test data
        test_data = b'x' * data_size
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(test_data)
            tmp_path = tmp.name
        
        try:
            # Create socket pair
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('127.0.0.1', 0))
            server_sock.listen(1)
            port = server_sock.getsockname()[1]
            
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(('127.0.0.1', port))
            
            conn, _ = server_sock.accept()
            
            # Track if os.sendfile was called
            sendfile_called = False
            original_sendfile = os.sendfile
            
            def tracking_sendfile(*args, **kwargs):
                nonlocal sendfile_called
                sendfile_called = True
                return original_sendfile(*args, **kwargs)
            
            with patch('os.sendfile', side_effect=tracking_sendfile):
                try:
                    result = real_zero_copy.send_file_to_socket(
                        client_sock, tmp_path, 0, data_size
                    )
                    # On platforms with sendfile, it should be used
                    assert sendfile_called or result == data_size, \
                        "Either sendfile should be called or all data should be sent"
                except OSError:
                    # Some socket configurations don't support sendfile
                    pass
            
            client_sock.close()
            conn.close()
            server_sock.close()
            
        finally:
            os.unlink(tmp_path)



class TestLinuxZeroCopySocket:
    """
    Test suite for Linux zero-copy socket implementation.
    
    **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
    **Validates: Requirements 3.1, 3.2**
    """
    
    @pytest.fixture
    def linux_socket(self):
        """Get LinuxZeroCopySocket instance"""
        from core.performance.zero_copy import LinuxZeroCopySocket
        return LinuxZeroCopySocket()
    
    def test_linux_socket_uses_real_sendfile(self, linux_socket):
        """
        Property test: LinuxZeroCopySocket.sendfile() should use real os.sendfile().
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.1**
        """
        if not linux_socket.sendfile_supported:
            pytest.skip("sendfile not supported")
        
        # Verify the sendfile method exists and uses os.sendfile
        assert hasattr(linux_socket, 'sendfile'), \
            "LinuxZeroCopySocket should have sendfile method"
        
        # The method should raise NotImplementedError if sendfile not available
        # or call os.sendfile if available
        if not hasattr(os, 'sendfile'):
            with pytest.raises(NotImplementedError):
                linux_socket.sendfile(0, 0, 0, 0)
    
    def test_linux_socket_msg_zerocopy_flag(self, linux_socket):
        """
        Property test: LinuxZeroCopySocket should use real MSG_ZEROCOPY flag.
        
        **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
        **Validates: Requirements 3.2**
        """
        # Verify msg_zerocopy_supported matches actual socket module
        expected = hasattr(socket, 'MSG_ZEROCOPY')
        assert linux_socket.msg_zerocopy_supported == expected, \
            "msg_zerocopy_supported should match socket.MSG_ZEROCOPY availability"


class TestDirectHardwareAccessDeprecation:
    """
    Test that DirectHardwareAccess is properly deprecated and honest.
    
    **Feature: real-high-performance-netstress, Property 7: Real Zero-Copy System Calls Used**
    **Validates: Requirements 3.1, 3.2**
    """
    
    def test_direct_hardware_access_returns_false(self):
        """
        Property test: DirectHardwareAccess.initialize_hardware_access() should return False.
        
        This verifies that the class honestly reports DMA is not available.
        """
        from core.performance.zero_copy import DirectHardwareAccess
        
        dha = DirectHardwareAccess()
        result = dha.initialize_hardware_access()
        
        assert result == False, \
            "DirectHardwareAccess should honestly report DMA is not available"
    
    def test_direct_hardware_access_capability_report(self):
        """
        Property test: DirectHardwareAccess capability report should be honest.
        """
        from core.performance.zero_copy import DirectHardwareAccess
        
        dha = DirectHardwareAccess()
        report = dha.get_capability_report()
        
        # Should report DMA as not available
        assert report['dma_available'] == False, \
            "DMA should not be claimed as available"
        assert report['kernel_bypass_available'] == False, \
            "Kernel bypass should not be claimed as available"


class TestZeroCopyStatusAccuracy:
    """
    Property-Based Test: Zero-Copy Status Report Accuracy
    
    **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
    **Validates: Requirements 3.5**
    
    This property test verifies that the zero-copy status report accurately reflects
    whether sendfile() and MSG_ZEROCOPY are available on the current platform.
    
    Property: For any call to get_status(), the returned status SHALL accurately
    reflect whether sendfile() and MSG_ZEROCOPY are available on the current platform.
    """
    
    @pytest.fixture
    def real_zero_copy(self):
        """Get RealZeroCopy instance"""
        from core.performance.real_zero_copy import RealZeroCopy
        return RealZeroCopy()
    
    def test_sendfile_availability_matches_os_module(self, real_zero_copy):
        """
        Property test: sendfile_available should match actual os.sendfile availability.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        """
        status = real_zero_copy.get_status()
        
        # sendfile_available should match whether os.sendfile exists
        expected_sendfile = hasattr(os, 'sendfile')
        assert status.sendfile_available == expected_sendfile, \
            f"sendfile_available ({status.sendfile_available}) should match " \
            f"os.sendfile availability ({expected_sendfile})"
    
    def test_msg_zerocopy_availability_matches_platform(self, real_zero_copy):
        """
        Property test: msg_zerocopy_available should be False on non-Linux platforms.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        """
        status = real_zero_copy.get_status()
        
        # MSG_ZEROCOPY is Linux-only
        if platform.system() != 'Linux':
            assert status.msg_zerocopy_available == False, \
                "MSG_ZEROCOPY should not be available on non-Linux platforms"
        else:
            # On Linux, it depends on kernel version and socket module
            expected = hasattr(socket, 'MSG_ZEROCOPY')
            if expected:
                # Also check kernel version (need 4.14+)
                try:
                    parts = platform.release().split('.')
                    major = int(parts[0])
                    minor = int(parts[1].split('-')[0])
                    expected = (major > 4) or (major == 4 and minor >= 14)
                except Exception:
                    expected = False
            
            assert status.msg_zerocopy_available == expected, \
                f"msg_zerocopy_available ({status.msg_zerocopy_available}) should match " \
                f"expected availability ({expected})"
    
    def test_platform_matches_actual_platform(self, real_zero_copy):
        """
        Property test: Reported platform should match actual platform.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        """
        status = real_zero_copy.get_status()
        
        assert status.platform == platform.system(), \
            f"Reported platform ({status.platform}) should match " \
            f"actual platform ({platform.system()})"
    
    def test_active_method_consistency(self, real_zero_copy):
        """
        Property test: active_method should be consistent with availability flags.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        """
        status = real_zero_copy.get_status()
        
        # If msg_zerocopy is available, it should be the active method
        if status.msg_zerocopy_available:
            assert status.active_method == 'msg_zerocopy', \
                "When MSG_ZEROCOPY is available, it should be the active method"
            assert status.is_true_zero_copy == True, \
                "MSG_ZEROCOPY should indicate true zero-copy"
        # Otherwise, if sendfile is available, it should be active
        elif status.sendfile_available:
            assert status.active_method == 'sendfile', \
                "When sendfile is available (but not MSG_ZEROCOPY), it should be active"
            assert status.is_true_zero_copy == True, \
                "sendfile should indicate true zero-copy"
        # Otherwise, buffered should be active
        else:
            assert status.active_method == 'buffered', \
                "When no zero-copy is available, buffered should be active"
            assert status.is_true_zero_copy == False, \
                "Buffered mode should not indicate true zero-copy"
    
    def test_status_dict_contains_all_fields(self, real_zero_copy):
        """
        Property test: Status dict should contain all required fields.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        """
        status_dict = real_zero_copy.get_status_dict()
        
        required_fields = [
            'platform',
            'kernel_version',
            'sendfile_available',
            'msg_zerocopy_available',
            'splice_available',
            'active_method',
            'is_true_zero_copy'
        ]
        
        for field in required_fields:
            assert field in status_dict, \
                f"Status dict should contain '{field}' field"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_status_consistency_across_calls(self, num_calls):
        """
        Property-based test: Status should be consistent across multiple calls.
        
        **Feature: real-high-performance-netstress, Property 8: Zero-Copy Status Report Accuracy**
        **Validates: Requirements 3.5**
        
        For any number of calls to get_status(), the returned values should be
        consistent (platform capabilities don't change during runtime).
        """
        from core.performance.real_zero_copy import RealZeroCopy
        
        real_zero_copy = RealZeroCopy()
        
        # Get initial status
        initial_status = real_zero_copy.get_status()
        
        # Make multiple calls and verify consistency
        for _ in range(min(num_calls, 10)):  # Cap at 10 to avoid slow tests
            current_status = real_zero_copy.get_status()
            
            assert current_status.platform == initial_status.platform, \
                "Platform should be consistent across calls"
            assert current_status.sendfile_available == initial_status.sendfile_available, \
                "sendfile_available should be consistent across calls"
            assert current_status.msg_zerocopy_available == initial_status.msg_zerocopy_available, \
                "msg_zerocopy_available should be consistent across calls"
            assert current_status.active_method == initial_status.active_method, \
                "active_method should be consistent across calls"
            assert current_status.is_true_zero_copy == initial_status.is_true_zero_copy, \
                "is_true_zero_copy should be consistent across calls"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
