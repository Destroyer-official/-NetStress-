"""
Property-Based Test: No False XDP/eBPF/DPDK Claims

**Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
**Validates: Requirements 5.1, 5.2, 5.3**

This property test verifies that the capability reporting system honestly reports
what is and isn't available. The system should never claim to have XDP, eBPF, or
DPDK capabilities unless they are actually implemented.

Property: For any capability report, the fields xdp, ebpf, and dpdk SHALL be False
unless actual BPF bytecode loading or DPDK driver binding is implemented.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest

try:
    from hypothesis import given, strategies as st, settings, assume, HealthCheck
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    HealthCheck = None
    # Provide fallback for when hypothesis is not installed
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip(reason="hypothesis not installed")(func)
        return decorator
    
    class st:
        @staticmethod
        def sampled_from(items):
            return items
        
        @staticmethod
        def integers(min_value=0, max_value=100):
            return range(min_value, max_value + 1)
    
    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def assume(condition):
        pass


def get_project_root() -> Path:
    """Get the NetStress project root directory."""
    # Navigate from tests directory to project root
    current = Path(__file__).parent.parent
    if current.name == '-NetStress-':
        return current
    # Try to find -NetStress- directory
    for parent in Path(__file__).parents:
        if parent.name == '-NetStress-':
            return parent
        netstress_dir = parent / '-NetStress-'
        if netstress_dir.exists():
            return netstress_dir
    return current


def import_capability_module():
    """Import the capability reporting module."""
    project_root = get_project_root()
    sys.path.insert(0, str(project_root))
    
    try:
        from core.capabilities.capability_report import CapabilityChecker, CapabilityReport, get_capabilities
        return CapabilityChecker, CapabilityReport, get_capabilities
    except ImportError as e:
        pytest.skip(f"Could not import capability module: {e}")


def check_for_real_xdp_implementation() -> bool:
    """
    Check if there's actual XDP implementation (BPF bytecode loading).
    
    Real XDP implementation would involve:
    - libbpf bindings
    - BPF program compilation
    - XDP program attachment to network interfaces
    """
    try:
        # Check for libbpf or bcc imports (actual usage, not just availability)
        import libbpf
        # If we can import it, check if it's actually used in the code
        project_root = get_project_root()
        py_files = list(project_root.rglob("*.py"))
        # Exclude test files to avoid detecting test code itself
        py_files = [f for f in py_files if not f.name.startswith('test_')]
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if "import libbpf" in content or "from libbpf" in content:
                    return True
            except:
                pass
    except ImportError:
        pass
    
    try:
        import bcc
        # Check if BCC is actually used
        project_root = get_project_root()
        py_files = list(project_root.rglob("*.py"))
        # Exclude test files to avoid detecting test code itself
        py_files = [f for f in py_files if not f.name.startswith('test_')]
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if "import bcc" in content or "from bcc" in content:
                    return True
            except:
                pass
    except ImportError:
        pass
    
    # Check for XDP-related system calls or kernel modules
    project_root = get_project_root()
    
    # Look for actual BPF program files (.c files with XDP sections)
    bpf_files = list(project_root.rglob("*.c"))
    for bpf_file in bpf_files:
        try:
            content = bpf_file.read_text()
            if "SEC(\"xdp\")" in content or "SEC('xdp')" in content:
                return True
        except:
            pass
    
    return False


def check_for_real_ebpf_implementation() -> bool:
    """
    Check if there's actual eBPF implementation.
    
    Real eBPF implementation would involve:
    - BPF program compilation and loading
    - Kernel interaction via bpf() syscall
    """
    try:
        # Check for eBPF libraries (actual usage, not just availability)
        import bcc
        # Check if BCC is actually used in the code
        project_root = get_project_root()
        py_files = list(project_root.rglob("*.py"))
        # Exclude test files to avoid detecting test code itself
        py_files = [f for f in py_files if not f.name.startswith('test_')]
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if "import bcc" in content or "from bcc" in content:
                    return True
            except:
                pass
    except ImportError:
        pass
    
    try:
        import libbpf
        # Check if libbpf is actually used
        project_root = get_project_root()
        py_files = list(project_root.rglob("*.py"))
        # Exclude test files to avoid detecting test code itself
        py_files = [f for f in py_files if not f.name.startswith('test_')]
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if "import libbpf" in content or "from libbpf" in content:
                    return True
            except:
                pass
    except ImportError:
        pass
    
    # Check for BPF program files
    project_root = get_project_root()
    bpf_files = list(project_root.rglob("*.c"))
    for bpf_file in bpf_files:
        try:
            content = bpf_file.read_text()
            if any(sec in content for sec in ["SEC(\"kprobe", "SEC(\"tracepoint", "SEC(\"socket"]):
                return True
        except:
            pass
    
    return False


def check_for_real_dpdk_implementation() -> bool:
    """
    Check if there's actual DPDK implementation.
    
    Real DPDK implementation would involve:
    - DPDK library bindings
    - NIC driver binding (igb_uio, vfio-pci)
    - Hugepage configuration
    """
    try:
        # Check for DPDK Python bindings
        import dpdk
        return True
    except ImportError:
        pass
    
    # Check for DPDK-related code patterns (actual implementation, not documentation)
    project_root = get_project_root()
    
    # Look for DPDK initialization patterns (actual code, not comments/docs)
    py_files = list(project_root.rglob("*.py"))
    
    # Exclude test files to avoid detecting test code itself
    py_files = [f for f in py_files if not f.name.startswith('test_')]
    
    for py_file in py_files:
        try:
            content = py_file.read_text()
            lines = content.split('\n')
            
            for line in lines:
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if '"""' in stripped or "'''" in stripped:
                    continue
                
                # Look for actual DPDK function calls (not in comments/docs)
                dpdk_patterns = [
                    "rte_eal_init(",
                    "rte_eth_dev_",
                    "rte_mempool_",
                    "dpdk.eal_init(",
                    "from dpdk import",
                    "import dpdk"
                ]
                
                if any(pattern in line for pattern in dpdk_patterns):
                    # Make sure it's not in a string literal that's just documentation
                    if not (line.strip().startswith('"') or line.strip().startswith("'")):
                        return True
        except:
            pass
    
    return False


class TestHonestCapabilityReporting:
    """Test suite for Property 10: No False XDP/eBPF/DPDK Claims"""
    
    @pytest.fixture
    def capability_classes(self):
        """Import capability reporting classes."""
        return import_capability_module()
    
    def test_xdp_claim_is_honest(self, capability_classes):
        """
        Test that XDP capability claim matches actual implementation.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.1**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        has_real_xdp = check_for_real_xdp_implementation()
        
        # The report should only claim XDP if it's actually implemented
        assert report.xdp == has_real_xdp, (
            f"XDP capability claim is dishonest: "
            f"reported={report.xdp}, actual_implementation={has_real_xdp}"
        )
        
        # Since we know XDP is not implemented in this codebase, it should be False
        assert report.xdp == False, (
            f"XDP should be False since no real XDP implementation exists, got {report.xdp}"
        )
    
    def test_ebpf_claim_is_honest(self, capability_classes):
        """
        Test that eBPF capability claim matches actual implementation.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.2**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        has_real_ebpf = check_for_real_ebpf_implementation()
        
        # The report should only claim eBPF if it's actually implemented
        assert report.ebpf == has_real_ebpf, (
            f"eBPF capability claim is dishonest: "
            f"reported={report.ebpf}, actual_implementation={has_real_ebpf}"
        )
        
        # Since we know eBPF is not implemented in this codebase, it should be False
        assert report.ebpf == False, (
            f"eBPF should be False since no real eBPF implementation exists, got {report.ebpf}"
        )
    
    def test_dpdk_claim_is_honest(self, capability_classes):
        """
        Test that DPDK capability claim matches actual implementation.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.3**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        has_real_dpdk = check_for_real_dpdk_implementation()
        
        # The report should only claim DPDK if it's actually implemented
        assert report.dpdk == has_real_dpdk, (
            f"DPDK capability claim is dishonest: "
            f"reported={report.dpdk}, actual_implementation={has_real_dpdk}"
        )
        
        # Since we know DPDK is not implemented in this codebase, it should be False
        assert report.dpdk == False, (
            f"DPDK should be False since no real DPDK implementation exists, got {report.dpdk}"
        )
    
    def test_kernel_bypass_claim_is_honest(self, capability_classes):
        """
        Test that kernel bypass capability claim is honest.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        # Kernel bypass requires XDP, eBPF, or DPDK
        has_kernel_bypass = (
            check_for_real_xdp_implementation() or
            check_for_real_ebpf_implementation() or
            check_for_real_dpdk_implementation()
        )
        
        assert report.kernel_bypass == has_kernel_bypass, (
            f"Kernel bypass capability claim is dishonest: "
            f"reported={report.kernel_bypass}, actual_implementation={has_kernel_bypass}"
        )
        
        # Since we know kernel bypass is not implemented, it should be False
        assert report.kernel_bypass == False, (
            f"Kernel bypass should be False since no real implementation exists, got {report.kernel_bypass}"
        )
    
    def test_recommendations_point_to_real_tools(self, capability_classes):
        """
        Test that recommendations point to real external tools for unimplemented features.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        recommendations_text = " ".join(report.recommendations).lower()
        
        # Should recommend real tools for unimplemented features
        if not report.dpdk:
            assert "dpdk" in recommendations_text, (
                "Should recommend DPDK when DPDK is not implemented"
            )
        
        if not report.xdp:
            assert "xdp" in recommendations_text, (
                "Should recommend XDP tools when XDP is not implemented"
            )
        
        # Should not claim these features are available when they're not
        assert not any(
            phrase in recommendations_text 
            for phrase in ["built-in xdp", "built-in ebpf", "built-in dpdk"]
        ), "Should not claim built-in support for unimplemented features"
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(call_count=st.integers(min_value=1, max_value=10))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_consistent_capability_claims_across_calls(self, call_count, capability_classes):
        """
        Property-based test: For any number of capability report calls,
        the XDP/eBPF/DPDK claims should be consistent.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        # Get multiple reports
        reports = []
        for _ in range(call_count):
            checker = CapabilityChecker()
            reports.append(checker.get_report())
        
        # All reports should have consistent claims
        first_report = reports[0]
        for i, report in enumerate(reports[1:], 1):
            assert report.xdp == first_report.xdp, (
                f"XDP claim inconsistent between calls: call 0 = {first_report.xdp}, "
                f"call {i} = {report.xdp}"
            )
            assert report.ebpf == first_report.ebpf, (
                f"eBPF claim inconsistent between calls: call 0 = {first_report.ebpf}, "
                f"call {i} = {report.ebpf}"
            )
            assert report.dpdk == first_report.dpdk, (
                f"DPDK claim inconsistent between calls: call 0 = {first_report.dpdk}, "
                f"call {i} = {report.dpdk}"
            )
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
    @given(feature=st.sampled_from(['xdp', 'ebpf', 'dpdk', 'kernel_bypass']))
    @settings(max_examples=4, suppress_health_check=[HealthCheck.function_scoped_fixture] if HYPOTHESIS_AVAILABLE else [])
    def test_property_no_false_claims_for_any_advanced_feature(self, feature, capability_classes):
        """
        Property-based test: For any advanced networking feature (XDP, eBPF, DPDK, kernel bypass),
        the capability report SHALL only claim the feature is available if it's actually implemented.
        
        **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        CapabilityChecker, CapabilityReport, get_capabilities = capability_classes
        
        checker = CapabilityChecker()
        report = checker.get_report()
        
        # Check that the feature is not falsely claimed
        feature_value = getattr(report, feature)
        
        # Since we know these features are not implemented in this codebase,
        # they should all be False
        assert feature_value == False, (
            f"Feature '{feature}' should be False since it's not actually implemented, "
            f"but capability report claims it's {feature_value}"
        )


def test_factory_function_returns_honest_report():
    """
    Test that the factory function returns an honest capability report.
    
    **Feature: real-high-performance-netstress, Property 10: No False XDP/eBPF/DPDK Claims**
    **Validates: Requirements 5.1, 5.2, 5.3**
    """
    CapabilityChecker, CapabilityReport, get_capabilities = import_capability_module()
    
    report = get_capabilities()
    
    # Should be a CapabilityReport instance
    assert isinstance(report, CapabilityReport), (
        f"get_capabilities() should return CapabilityReport, got {type(report)}"
    )
    
    # Should have honest claims about advanced features
    assert report.xdp == False, f"XDP should be False, got {report.xdp}"
    assert report.ebpf == False, f"eBPF should be False, got {report.ebpf}"
    assert report.dpdk == False, f"DPDK should be False, got {report.dpdk}"
    assert report.kernel_bypass == False, f"Kernel bypass should be False, got {report.kernel_bypass}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])