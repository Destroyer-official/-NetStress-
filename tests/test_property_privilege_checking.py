"""
Property-Based Test: Privilege Check Before Privileged Operations

**Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
**Validates: Requirements 1.5, 4.4, 4.5**

This property test verifies that the system checks privileges before attempting
privileged operations and provides clear error messages if insufficient.

Property: For any operation requiring root/admin privileges, the system SHALL
check privileges first and provide a clear error message if insufficient.
"""

import os
import sys
import platform
from pathlib import Path
from typing import List

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
        def sampled_from(items):
            return items[0] if items else None
        
        @staticmethod
        def text(min_size=1, max_size=10):
            return "test"
    
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


# Privileged operations that require root/admin
PRIVILEGED_OPERATIONS = [
    'sysctl',
    'raw_socket',
    'interface_config',
    'netsh',
    'registry',
    'traffic_control',
]

# User-space operations that don't require root
USER_SPACE_OPERATIONS = [
    'socket_buffer',
    'tcp_nodelay',
    'tcp_quickack',
    'so_reuseaddr',
    'so_reuseport',
    'nonblocking',
]


class TestPrivilegeChecking:
    """
    Test suite for Property 3: Privilege Check Before Privileged Operations
    
    **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
    **Validates: Requirements 1.5, 4.4, 4.5**
    """
    
    @pytest.fixture
    def optimizer(self):
        """Create a RealKernelOptimizer instance for testing."""
        from core.performance.real_kernel_opts import RealKernelOptimizer
        return RealKernelOptimizer()
    
    def test_privilege_check_exists(self, optimizer):
        """
        Property test: Optimizer should have privilege checking capability.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5**
        """
        # Verify the optimizer has privilege checking methods
        assert hasattr(optimizer, 'is_root'), "Optimizer should have is_root attribute"
        assert hasattr(optimizer, '_check_root'), "Optimizer should have _check_root method"
        assert hasattr(optimizer, 'check_privilege_for_operation'), "Optimizer should have check_privilege_for_operation method"
        
        # is_root should be a boolean
        assert isinstance(optimizer.is_root, bool), "is_root should be a boolean"
    
    def test_privilege_check_returns_correct_type(self, optimizer):
        """
        Property test: check_privilege_for_operation should return (bool, str) tuple.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5, 4.4**
        """
        result = optimizer.check_privilege_for_operation('sysctl')
        
        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 2, "Tuple should have 2 elements"
        assert isinstance(result[0], bool), "First element should be boolean"
        assert isinstance(result[1], str), "Second element should be string"
    
    def test_user_space_operations_always_allowed(self, optimizer):
        """
        Property test: User-space operations should always be allowed.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 4.5**
        """
        for operation in USER_SPACE_OPERATIONS:
            has_privilege, message = optimizer.check_privilege_for_operation(operation)
            
            assert has_privilege == True, \
                f"User-space operation '{operation}' should always be allowed, got: {message}"
            assert "no special privileges" in message.lower() or "user-space" in message.lower(), \
                f"Message should indicate no special privileges needed for '{operation}'"
    
    def test_privileged_operations_check_root(self, optimizer):
        """
        Property test: Privileged operations should check for root/admin.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5, 4.4**
        """
        for operation in PRIVILEGED_OPERATIONS:
            has_privilege, message = optimizer.check_privilege_for_operation(operation)
            
            if optimizer.is_root:
                # If running as root, should be allowed
                assert has_privilege == True, \
                    f"Privileged operation '{operation}' should be allowed when running as root"
            else:
                # If not root, should be denied with instructions
                assert has_privilege == False, \
                    f"Privileged operation '{operation}' should be denied when not root"
                # Message should contain instructions
                assert len(message) > 0, \
                    f"Should provide instructions for '{operation}' when not root"
    
    def test_privilege_instructions_are_helpful(self, optimizer):
        """
        Property test: Privilege denial messages should contain helpful instructions.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 4.4**
        """
        if optimizer.is_root:
            pytest.skip("Cannot test denial messages when running as root")
        
        has_privilege, message = optimizer.check_privilege_for_operation('sysctl')
        
        assert has_privilege == False, "Should deny sysctl without root"
        
        # Message should contain platform-appropriate instructions
        current_platform = platform.system()
        
        if current_platform == 'Linux':
            assert 'sudo' in message.lower(), \
                "Linux instructions should mention sudo"
        elif current_platform == 'Windows':
            assert 'administrator' in message.lower(), \
                "Windows instructions should mention Administrator"
        elif current_platform == 'Darwin':
            assert 'sudo' in message.lower(), \
                "macOS instructions should mention sudo"
    
    def test_sysctl_checks_privilege_before_execution(self, optimizer):
        """
        Property test: apply_sysctl should check privileges and fail gracefully.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5, 4.4**
        """
        if platform.system() != 'Linux':
            pytest.skip("sysctl only available on Linux")
        
        # Try to apply a sysctl setting
        result = optimizer.apply_sysctl('net.core.rmem_max', '16777216')
        
        if optimizer.is_root:
            # May succeed or fail based on system, but should attempt
            assert result.name == 'sysctl:net.core.rmem_max'
        else:
            # Should fail with clear message about needing root
            assert result.success == False, "Should fail without root"
            assert result.requires_root == True, "Should indicate root is required"
            assert 'root' in result.error.lower() or 'sudo' in result.error.lower(), \
                f"Error should mention root/sudo, got: {result.error}"
    
    def test_user_space_mode_info(self, optimizer):
        """
        Property test: get_user_space_mode_info should provide complete information.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 4.5**
        """
        info = optimizer.get_user_space_mode_info()
        
        # Should have all required fields
        assert 'is_user_space_mode' in info, "Should have is_user_space_mode"
        assert 'is_root' in info, "Should have is_root"
        assert 'platform' in info, "Should have platform"
        assert 'available_without_root' in info, "Should have available_without_root"
        assert 'requires_root' in info, "Should have requires_root"
        assert 'instructions' in info, "Should have instructions"
        
        # Types should be correct
        assert isinstance(info['is_user_space_mode'], bool)
        assert isinstance(info['is_root'], bool)
        assert isinstance(info['platform'], str)
        assert isinstance(info['available_without_root'], list)
        assert isinstance(info['requires_root'], list)
        assert isinstance(info['instructions'], str)
        
        # User-space mode should be opposite of is_root
        assert info['is_user_space_mode'] == (not info['is_root']), \
            "User-space mode should be active when not root"
    
    def test_capability_report_reflects_privileges(self, optimizer):
        """
        Property test: Capability report should accurately reflect privilege status.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5, 4.5**
        """
        report = optimizer.get_capability_report()
        
        # Report should have is_root field
        assert hasattr(report, 'is_root'), "Report should have is_root"
        assert report.is_root == optimizer.is_root, \
            "Report is_root should match optimizer is_root"
        
        # If not root, sysctl should not be available on Linux
        if platform.system() == 'Linux' and not optimizer.is_root:
            assert report.sysctl_available == False, \
                "sysctl should not be available without root on Linux"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(operation=st.sampled_from(PRIVILEGED_OPERATIONS + USER_SPACE_OPERATIONS))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_privilege_check_for_any_operation(self, operation):
        """
        Property-based test: For any operation, check_privilege_for_operation
        SHALL return a valid (bool, str) tuple and provide appropriate response.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5, 4.4, 4.5**
        """
        from core.performance.real_kernel_opts import RealKernelOptimizer
        
        optimizer = RealKernelOptimizer()
        has_privilege, message = optimizer.check_privilege_for_operation(operation)
        
        # Should always return valid types
        assert isinstance(has_privilege, bool), f"has_privilege should be bool for '{operation}'"
        assert isinstance(message, str), f"message should be str for '{operation}'"
        assert len(message) > 0, f"message should not be empty for '{operation}'"
        
        # User-space operations should always be allowed
        if operation in USER_SPACE_OPERATIONS:
            assert has_privilege == True, \
                f"User-space operation '{operation}' should always be allowed"
        
        # Privileged operations depend on root status
        if operation in PRIVILEGED_OPERATIONS:
            if optimizer.is_root:
                assert has_privilege == True, \
                    f"Privileged operation '{operation}' should be allowed when root"
            else:
                assert has_privilege == False, \
                    f"Privileged operation '{operation}' should be denied when not root"


class TestPrivilegeCheckIntegration:
    """Integration tests for privilege checking across the system."""
    
    def test_optimizer_initialization_checks_privileges(self):
        """
        Test that optimizer checks privileges during initialization.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 1.5**
        """
        from core.performance.real_kernel_opts import RealKernelOptimizer
        
        optimizer = RealKernelOptimizer()
        
        # Should have determined privilege status
        assert hasattr(optimizer, 'is_root')
        assert hasattr(optimizer, '_user_space_mode')
        
        # User-space mode should be set correctly
        assert optimizer._user_space_mode == (not optimizer.is_root)
    
    def test_apply_all_optimizations_respects_privileges(self):
        """
        Test that apply_all_optimizations respects privilege levels.
        
        **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
        **Validates: Requirements 4.4, 4.5**
        """
        from core.performance.real_kernel_opts import RealKernelOptimizer
        
        optimizer = RealKernelOptimizer()
        report = optimizer.apply_all_optimizations()
        
        # Report should reflect what was actually applied
        if not optimizer.is_root:
            # Without root, kernel-level optimizations should be skipped
            for skipped in report.skipped:
                assert 'root' in skipped.lower() or 'requires' in skipped.lower(), \
                    f"Skipped items should mention root requirement: {skipped}"


def test_privilege_check_comprehensive():
    """
    Comprehensive test for privilege checking functionality.
    
    **Feature: real-high-performance-netstress, Property 3: Privilege Check Before Privileged Operations**
    **Validates: Requirements 1.5, 4.4, 4.5**
    """
    from core.performance.real_kernel_opts import RealKernelOptimizer
    
    optimizer = RealKernelOptimizer()
    
    print(f"\nPrivilege Check Test Results:")
    print(f"  Platform: {optimizer.platform}")
    print(f"  Is Root: {optimizer.is_root}")
    print(f"  User-Space Mode: {optimizer._user_space_mode}")
    
    # Test all operations
    print(f"\n  Operation Checks:")
    for op in PRIVILEGED_OPERATIONS + USER_SPACE_OPERATIONS:
        has_priv, msg = optimizer.check_privilege_for_operation(op)
        status = "✓" if has_priv else "✗"
        print(f"    {status} {op}: {has_priv}")
    
    # Get user-space mode info
    info = optimizer.get_user_space_mode_info()
    print(f"\n  Available without root: {len(info['available_without_root'])} optimizations")
    print(f"  Requires root: {len(info['requires_root'])} optimizations")
    
    # Verify the property holds
    for op in USER_SPACE_OPERATIONS:
        has_priv, _ = optimizer.check_privilege_for_operation(op)
        assert has_priv == True, f"User-space operation {op} should always be allowed"
    
    for op in PRIVILEGED_OPERATIONS:
        has_priv, _ = optimizer.check_privilege_for_operation(op)
        if optimizer.is_root:
            assert has_priv == True, f"Privileged operation {op} should be allowed when root"
        else:
            assert has_priv == False, f"Privileged operation {op} should be denied when not root"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
