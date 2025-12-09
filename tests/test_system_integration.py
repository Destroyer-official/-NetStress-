#!/usr/bin/env python3
"""
System Integration Tests - Final validation and acceptance testing
Simplified tests that work with the actual implementation
"""

import pytest
import asyncio
import logging
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class TestCoreComponents:
    """Test core component availability and basic functionality"""
    
    def test_safety_manager_import(self):
        """Test SafetyManager can be imported and instantiated"""
        from core.safety.protection_mechanisms import SafetyManager, ResourceLimits
        
        limits = ResourceLimits(max_duration_minutes=1)
        manager = SafetyManager(limits)
        
        assert manager is not None
        assert manager.safety_enabled
    
    def test_target_validator_import(self):
        """Test TargetValidator can be imported and used"""
        from core.safety.protection_mechanisms import TargetValidator
        
        validator = TargetValidator()
        
        # Test safe IP validation
        is_safe, reason, info = validator.validate_target("127.0.0.1", 80)
        assert is_safe
        assert info.risk_level == 'low'
    
    def test_audit_logger_import(self):
        """Test AuditLogger can be imported"""
        from core.safety.audit_logging import AuditLogger
        
        # Just test import works
        assert AuditLogger is not None
    
    def test_platform_engine_import(self):
        """Test PlatformEngine can be imported and instantiated"""
        from core.platform.abstraction import PlatformEngine
        
        engine = PlatformEngine()
        
        assert engine is not None
        assert engine.system_info is not None
    
    def test_tcp_engine_import(self):
        """Test TCPEngine can be imported and instantiated"""
        from core.networking.tcp_engine import TCPEngine, TCPAttackConfig
        
        config = TCPAttackConfig(target="127.0.0.1", port=80)
        engine = TCPEngine(config)
        
        assert engine is not None
        assert engine.config.target == "127.0.0.1"
    
    def test_udp_engine_import(self):
        """Test UDPEngine can be imported and instantiated"""
        from core.networking.udp_engine import ExtremeUDPEngine, UDPAttackConfig
        
        config = UDPAttackConfig(target="127.0.0.1", port=80)
        engine = ExtremeUDPEngine(config)
        
        assert engine is not None


class TestSafetyIntegration:
    """Test safety system integration"""
    
    def test_target_validation_safe_ips(self):
        """Test target validation for safe IPs"""
        from core.safety.protection_mechanisms import SafetyManager
        
        manager = SafetyManager()
        
        # Test safe targets
        safe_targets = [
            ("127.0.0.1", 80),
            ("192.168.1.1", 8080),
            ("10.0.0.1", 443),
        ]
        
        for target, port in safe_targets:
            is_valid, reason = manager.validate_attack_request(target, port, "TCP")
            assert is_valid, f"Target {target}:{port} should be valid: {reason}"
    
    def test_target_validation_blocked_ips(self):
        """Test target validation blocks production systems"""
        from core.safety.protection_mechanisms import SafetyManager
        
        manager = SafetyManager()
        
        # Test blocked targets
        blocked_targets = [
            ("google.com", 80),
            ("github.com", 443),
        ]
        
        for target, port in blocked_targets:
            is_valid, reason = manager.validate_attack_request(target, port, "TCP")
            assert not is_valid, f"Target {target}:{port} should be blocked"
    
    def test_resource_monitor_creation(self):
        """Test ResourceMonitor can be created"""
        from core.safety.protection_mechanisms import ResourceMonitor, ResourceLimits
        
        limits = ResourceLimits(
            max_cpu_percent=80.0,
            max_memory_percent=70.0,
            max_duration_minutes=60
        )
        
        monitor = ResourceMonitor(limits)
        
        assert monitor is not None
        assert not monitor.monitoring
    
    def test_emergency_shutdown_creation(self):
        """Test EmergencyShutdown can be created"""
        from core.safety.emergency_shutdown import EmergencyShutdown
        
        shutdown = EmergencyShutdown()
        
        assert shutdown is not None
        assert not shutdown.shutdown_triggered


class TestPlatformIntegration:
    """Test platform abstraction integration"""
    
    def test_platform_detection(self):
        """Test platform detection works"""
        from core.platform.detection import PlatformDetector, PlatformType
        
        platform_type = PlatformDetector.detect_platform()
        
        assert platform_type is not None
        assert isinstance(platform_type, PlatformType)
    
    def test_system_info_retrieval(self):
        """Test system info can be retrieved"""
        from core.platform.detection import PlatformDetector
        
        system_info = PlatformDetector.get_system_info()
        
        assert system_info is not None
        assert system_info.cpu_count > 0
    
    def test_network_capabilities(self):
        """Test network capabilities detection"""
        from core.platform.abstraction import PlatformEngine
        
        engine = PlatformEngine()
        capabilities = engine.get_network_capabilities()
        
        assert isinstance(capabilities, dict)
        assert 'raw_sockets' in capabilities
        assert 'async_io' in capabilities


class TestNetworkingIntegration:
    """Test networking components integration"""
    
    @pytest.mark.asyncio
    async def test_tcp_packet_creation(self):
        """Test TCP packet creation"""
        from core.networking.tcp_engine import TCPEngine, TCPAttackConfig, TCPAttackType
        
        config = TCPAttackConfig(target="127.0.0.1", port=80)
        engine = TCPEngine(config)
        
        packet = await engine.create_packet(
            "127.0.0.1", 80, 64, TCPAttackType.SYN_FLOOD
        )
        
        assert packet is not None
        assert len(packet) > 0
    
    def test_udp_payload_generation(self):
        """Test UDP payload generation"""
        from core.networking.udp_engine import UDPPayloadGenerator
        
        payload = UDPPayloadGenerator.random_payload(1024)
        
        assert payload is not None
        assert len(payload) == 1024
    
    def test_http_payload_generation(self):
        """Test HTTP payload generation"""
        from core.networking.http_engine import HTTPPayloadGenerator
        
        request = HTTPPayloadGenerator.generate_http1_request("example.com", 80)
        
        assert request is not None
        assert "GET" in request
        assert "Host:" in request


class TestDocumentation:
    """Test documentation completeness"""
    
    def test_readme_exists(self):
        """Test README.md exists"""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md not found"
    
    def test_requirements_exists(self):
        """Test requirements.txt exists"""
        req_path = Path(__file__).parent.parent / "requirements.txt"
        assert req_path.exists(), "requirements.txt not found"
    
    def test_docs_directory_exists(self):
        """Test docs directory exists"""
        docs_path = Path(__file__).parent.parent / "docs"
        assert docs_path.exists(), "docs directory not found"


class TestEndToEndWorkflow:
    """Test end-to-end workflow"""
    
    def test_complete_validation_workflow(self):
        """Test complete target validation workflow"""
        from core.safety.protection_mechanisms import SafetyManager
        from core.platform.abstraction import PlatformEngine
        
        # Initialize components
        safety_manager = SafetyManager()
        platform_engine = PlatformEngine()
        
        # Get system info
        system_info = platform_engine.get_system_info()
        assert system_info is not None
        
        # Validate a safe target
        is_valid, reason = safety_manager.validate_attack_request(
            "127.0.0.1", 8080, "TCP"
        )
        assert is_valid
        
        # Get safety status
        status = safety_manager.get_safety_status()
        assert status['safety_enabled']
    
    @pytest.mark.asyncio
    async def test_attack_engine_workflow(self):
        """Test attack engine initialization workflow"""
        from core.networking.tcp_engine import TCPEngine, TCPAttackConfig
        
        # Create and configure engine
        config = TCPAttackConfig(
            target="127.0.0.1",
            port=8080,
            max_connections=10
        )
        engine = TCPEngine(config)
        
        # Get status
        status = await engine.get_status()
        assert status['initialized']
        
        # Get supported attacks
        attacks = engine.get_supported_attacks()
        assert 'syn_flood' in attacks


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
