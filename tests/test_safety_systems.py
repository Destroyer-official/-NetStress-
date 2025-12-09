#!/usr/bin/env python3
"""
Safety Systems Testing
Comprehensive tests for safety, security, and ethical controls
"""

import os
import sys
import time
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add core to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.safety.protection_mechanisms import (
    SafetyManager, TargetValidator, ResourceMonitor, ResourceLimits
)
from core.safety.emergency_shutdown import EmergencyShutdown, ShutdownTrigger
from core.safety.environment_detection import EnvironmentDetector, EnvironmentInfo
from core.safety.audit_logging import AuditLogger, AuditEvent, AttackSession

class TestTargetValidator(unittest.TestCase):
    """Test target validation functionality"""
    
    def setUp(self):
        self.validator = TargetValidator()
    
    def test_safe_ip_ranges(self):
        """Test validation of safe IP ranges"""
        # Test private IP ranges
        safe_ips = [
            '192.168.1.1',
            '10.0.0.1', 
            '172.16.0.1',
            '127.0.0.1'
        ]
        
        for ip in safe_ips:
            is_safe, reason, target_info = self.validator.validate_target(ip, 80)
            self.assertTrue(is_safe, f"IP {ip} should be safe: {reason}")
            self.assertEqual(target_info.risk_level, 'low')
    
    def test_production_indicators(self):
        """Test detection of production system indicators"""
        # Test production domains
        production_targets = [
            'google.com',
            'github.com',
            'amazonaws.com'
        ]
        
        for target in production_targets:
            is_safe, reason, target_info = self.validator.validate_target(target, 80)
            self.assertFalse(is_safe, f"Target {target} should be blocked: {reason}")
            self.assertTrue(target_info.is_production)
    
    def test_blocked_targets(self):
        """Test blocked targets functionality"""
        # Add a target to blocked list
        self.validator.blocked_targets.add('blocked.example.com')
        
        is_safe, reason, target_info = self.validator.validate_target('blocked.example.com', 80)
        self.assertFalse(is_safe)
        self.assertIn('blocked list', reason)
    
    def test_port_validation(self):
        """Test port-based validation"""
        # Test common production ports
        production_ports = [22, 80, 443]
        
        for port in production_ports:
            # Should still pass for safe IPs even with production ports
            is_safe, reason, target_info = self.validator.validate_target('192.168.1.1', port)
            self.assertTrue(is_safe)

class TestResourceMonitor(unittest.TestCase):
    """Test resource monitoring functionality"""
    
    def setUp(self):
        self.limits = ResourceLimits(
            max_cpu_percent=50.0,
            max_memory_percent=50.0,
            max_duration_minutes=1
        )
        self.monitor = ResourceMonitor(self.limits)
        self.shutdown_called = False
        
    def shutdown_callback(self, reason):
        self.shutdown_called = True
        self.shutdown_reason = reason
    
    def test_resource_monitoring_start_stop(self):
        """Test starting and stopping resource monitoring"""
        self.assertFalse(self.monitor.monitoring)
        
        self.monitor.start_monitoring(self.shutdown_callback)
        self.assertTrue(self.monitor.monitoring)
        
        time.sleep(0.1)  # Let it run briefly
        
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring)
    
    @patch('psutil.cpu_percent')
    def test_cpu_limit_violation(self, mock_cpu):
        """Test CPU limit violation detection"""
        mock_cpu.return_value = 95.0  # Above limit
        
        self.monitor.start_monitoring(self.shutdown_callback)
        time.sleep(2)  # Wait for monitoring to detect violation
        self.monitor.stop_monitoring()
        
        self.assertGreater(self.monitor.violation_count, 0)
    
    def test_duration_limit(self):
        """Test duration limit enforcement"""
        # Set very short duration for testing
        self.limits.max_duration_minutes = 0.01  # 0.6 seconds
        
        self.monitor.start_monitoring(self.shutdown_callback)
        # Wait longer than limit - need enough time for monitoring thread to check
        time.sleep(3)
        self.monitor.stop_monitoring()
        
        # Should trigger shutdown
        self.assertTrue(self.shutdown_called)
        self.assertIn('Duration limit', self.shutdown_reason)
    
    def test_get_current_usage(self):
        """Test getting current resource usage"""
        usage = self.monitor.get_current_usage()
        
        self.assertIn('cpu_percent', usage)
        self.assertIn('memory_percent', usage)
        self.assertIsInstance(usage['cpu_percent'], (int, float))

class TestEmergencyShutdown(unittest.TestCase):
    """Test emergency shutdown functionality"""
    
    def setUp(self):
        self.shutdown = EmergencyShutdown()
        self.callback_called = False
        
    def shutdown_callback(self, reason):
        self.callback_called = True
        self.callback_reason = reason
    
    def test_manual_shutdown(self):
        """Test manual shutdown trigger"""
        self.shutdown.register_shutdown_callback(self.shutdown_callback)
        
        self.assertFalse(self.shutdown.shutdown_triggered)
        
        self.shutdown.manual_shutdown()
        
        self.assertTrue(self.shutdown.shutdown_triggered)
        self.assertTrue(self.callback_called)
        self.assertEqual(self.callback_reason, "Manual shutdown requested")
    
    def test_custom_trigger(self):
        """Test custom shutdown trigger"""
        # Use a mutable container to allow closure to see updates
        trigger_state = {'activated': False}
        
        def custom_trigger():
            return trigger_state['activated']
        
        trigger = ShutdownTrigger(
            name="test_trigger",
            condition=custom_trigger,
            priority=1,
            description="Test trigger"
        )
        
        self.shutdown.add_trigger(trigger)
        self.shutdown.register_shutdown_callback(self.shutdown_callback)
        
        # Start monitoring
        self.shutdown.start_monitoring()
        
        # Give monitoring thread time to start
        time.sleep(0.5)
        
        # Activate trigger
        trigger_state['activated'] = True
        
        # Wait for monitoring to detect (with longer timeout)
        time.sleep(3)
        
        self.assertTrue(self.shutdown.shutdown_triggered)
        self.assertTrue(self.callback_called)
        
        self.shutdown.stop_monitoring()
    
    def test_process_tracking(self):
        """Test process tracking functionality"""
        test_pid = 12345
        
        self.shutdown.track_process(test_pid, "Test process", "test_attack")
        
        self.assertIn(test_pid, self.shutdown.tracked_processes)
        self.assertEqual(self.shutdown.tracked_processes[test_pid]['description'], "Test process")
        
        self.shutdown.untrack_process(test_pid)
        self.assertNotIn(test_pid, self.shutdown.tracked_processes)
    
    def test_shutdown_status(self):
        """Test shutdown status reporting"""
        status = self.shutdown.get_shutdown_status()
        
        self.assertIn('shutdown_triggered', status)
        self.assertIn('monitoring_active', status)
        self.assertIn('tracked_processes', status)
        self.assertIsInstance(status['shutdown_triggered'], bool)

class TestEnvironmentDetector(unittest.TestCase):
    """Test environment detection functionality"""
    
    def setUp(self):
        self.detector = EnvironmentDetector()
    
    def test_environment_detection(self):
        """Test basic environment detection"""
        env_info = self.detector.detect_environment()
        
        self.assertIsInstance(env_info, EnvironmentInfo)
        self.assertIsInstance(env_info.is_virtual, bool)
        self.assertIsInstance(env_info.confidence_level, float)
        self.assertIn(env_info.risk_level, ['safe', 'caution', 'danger'])
    
    @patch('os.path.exists')
    def test_docker_detection(self, mock_exists):
        """Test Docker environment detection"""
        # Mock Docker environment
        mock_exists.side_effect = lambda path: path == '/.dockerenv'
        
        result = self.detector._detect_docker()
        
        self.assertIsNotNone(result)
        virt_type, confidence, indicators = result
        self.assertEqual(virt_type, "Docker")
        self.assertGreater(confidence, 0)
        self.assertIn("Docker indicator found: /.dockerenv", indicators)
    
    @patch('platform.system')
    @patch('builtins.open', create=True)
    def test_wsl_detection(self, mock_open, mock_system):
        """Test WSL detection"""
        mock_system.return_value = "Linux"
        mock_open.return_value.__enter__.return_value.read.return_value = "Microsoft WSL"
        
        with patch('os.path.exists', return_value=True):
            result = self.detector._detect_wsl()
        
        self.assertIsNotNone(result)
        virt_type, confidence, indicators = result
        self.assertEqual(virt_type, "WSL")
    
    def test_safe_environment_check(self):
        """Test safe environment validation"""
        is_safe, reason = self.detector.is_safe_environment()
        
        # Result depends on actual environment, but should return valid response
        self.assertIsInstance(is_safe, bool)
        self.assertIsInstance(reason, str)
    
    def test_environment_report(self):
        """Test environment report generation"""
        report = self.detector.get_environment_report()
        
        self.assertIn('timestamp', report)
        self.assertIn('platform', report)
        self.assertIn('virtualization', report)
        self.assertIn('restrictions', report)
        self.assertIn('safety_status', report)

class TestAuditLogging(unittest.TestCase):
    """Test audit logging functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.audit_logger = AuditLogger(self.temp_dir)
    
    def tearDown(self):
        # Cleanup temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_audit_event_logging(self):
        """Test basic audit event logging"""
        session_id = "test_session_123"
        
        # Log attack start
        self.audit_logger.log_attack_start(
            session_id=session_id,
            target="192.168.1.100",
            port=80,
            protocol="TCP",
            attack_type="flood",
            parameters={"packet_size": 1024},
            environment_info={"is_virtual": True},
            safety_checks={"target_safe": True}
        )
        
        # Log some activity
        self.audit_logger.log_attack_activity(
            session_id=session_id,
            action="packet_sent",
            packets=100,
            bytes_sent=102400
        )
        
        # Log attack end
        self.audit_logger.log_attack_end(session_id, "completed")
        
        # Verify session was tracked
        report = self.audit_logger.secure_logger.get_session_report(session_id)
        self.assertIsNotNone(report)
        self.assertEqual(report['session']['session_id'], session_id)
    
    def test_safety_violation_logging(self):
        """Test safety violation logging"""
        self.audit_logger.log_safety_violation(
            violation_type="target_validation_failed",
            description="Attempted to target production system",
            target="production.example.com"
        )
        
        # Should be logged as critical event
        # In a real implementation, we'd query the database to verify
    
    def test_report_generation(self):
        """Test report generation"""
        # Generate compliance report
        report = self.audit_logger.generate_report("compliance")
        
        self.assertIn('report_type', report)
        self.assertIn('compliance_metrics', report)
        self.assertEqual(report['report_type'], 'compliance_report')
    
    def test_encrypted_logging(self):
        """Test that sensitive data is encrypted"""
        # This is a basic test - in practice, we'd verify encryption
        secure_logger = self.audit_logger.secure_logger
        
        test_data = "sensitive_information"
        encrypted = secure_logger._encrypt_sensitive_data(test_data)
        decrypted = secure_logger._decrypt_sensitive_data(encrypted)
        
        self.assertNotEqual(test_data, encrypted)
        self.assertEqual(test_data, decrypted)

class TestSafetyManager(unittest.TestCase):
    """Test overall safety management"""
    
    def setUp(self):
        self.limits = ResourceLimits(max_duration_minutes=1)
        self.safety_manager = SafetyManager(self.limits)
    
    def test_attack_validation(self):
        """Test attack request validation"""
        # Test safe target
        is_valid, reason = self.safety_manager.validate_attack_request(
            target="192.168.1.100",
            port=80,
            protocol="TCP",
            duration=30
        )
        self.assertTrue(is_valid)
        
        # Test unsafe target
        is_valid, reason = self.safety_manager.validate_attack_request(
            target="google.com",
            port=80,
            protocol="TCP",
            duration=30
        )
        self.assertFalse(is_valid)
    
    def test_attack_monitoring(self):
        """Test attack monitoring lifecycle"""
        attack_id = "test_attack_123"
        
        # Start monitoring
        self.safety_manager.start_attack_monitoring(attack_id, "192.168.1.100", 80)
        self.assertIn(attack_id, self.safety_manager.active_attacks)
        
        # Stop monitoring
        self.safety_manager.stop_attack_monitoring(attack_id)
        self.assertNotIn(attack_id, self.safety_manager.active_attacks)
    
    def test_emergency_shutdown(self):
        """Test emergency shutdown functionality"""
        shutdown_called = False
        
        def shutdown_callback(reason):
            nonlocal shutdown_called
            shutdown_called = True
        
        self.safety_manager.register_shutdown_callback(shutdown_callback)
        
        # Trigger emergency shutdown
        self.safety_manager.emergency_shutdown("Test emergency")
        
        self.assertTrue(self.safety_manager.emergency_shutdown_triggered)
        self.assertTrue(shutdown_called)
    
    def test_safety_status(self):
        """Test safety status reporting"""
        status = self.safety_manager.get_safety_status()
        
        self.assertIn('safety_enabled', status)
        self.assertIn('emergency_shutdown_triggered', status)
        self.assertIn('active_attacks', status)
        self.assertIsInstance(status['safety_enabled'], bool)
    
    def test_safety_disable_enable(self):
        """Test disabling and enabling safety controls"""
        # Test invalid disable code
        result = self.safety_manager.disable_safety("invalid_code")
        self.assertFalse(result)
        self.assertTrue(self.safety_manager.safety_enabled)
        
        # Test valid disable code
        valid_code = "DISABLE_SAFETY_CONTROLS_I_UNDERSTAND_THE_RISKS"
        result = self.safety_manager.disable_safety(valid_code)
        self.assertTrue(result)
        self.assertFalse(self.safety_manager.safety_enabled)
        
        # Re-enable safety
        self.safety_manager.enable_safety()
        self.assertTrue(self.safety_manager.safety_enabled)

class TestIntegration(unittest.TestCase):
    """Integration tests for safety systems"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.safety_manager = SafetyManager()
        self.audit_logger = AuditLogger(self.temp_dir)
        self.emergency_shutdown = EmergencyShutdown()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_safety_workflow(self):
        """Test complete safety workflow"""
        # 1. Validate environment
        detector = EnvironmentDetector()
        env_info = detector.detect_environment()
        
        # 2. Validate target
        is_valid, reason = self.safety_manager.validate_attack_request(
            target="192.168.1.100",
            port=80,
            protocol="TCP"
        )
        
        if is_valid:
            # 3. Start attack monitoring
            attack_id = "integration_test_123"
            self.safety_manager.start_attack_monitoring(attack_id, "192.168.1.100", 80)
            
            # 4. Log attack start
            self.audit_logger.log_attack_start(
                session_id=attack_id,
                target="192.168.1.100",
                port=80,
                protocol="TCP",
                attack_type="test",
                parameters={},
                environment_info=env_info.__dict__,
                safety_checks={"validated": True}
            )
            
            # 5. Simulate some activity
            self.audit_logger.log_attack_activity(
                session_id=attack_id,
                action="test_packet",
                packets=10,
                bytes_sent=1024
            )
            
            # 6. End attack
            self.safety_manager.stop_attack_monitoring(attack_id)
            self.audit_logger.log_attack_end(attack_id, "completed")
            
            # 7. Verify everything was logged
            report = self.audit_logger.secure_logger.get_session_report(attack_id)
            self.assertIsNotNone(report)
    
    def test_safety_violation_handling(self):
        """Test handling of safety violations"""
        # Register callbacks
        violation_detected = False
        
        def violation_callback(reason):
            nonlocal violation_detected
            violation_detected = True
        
        self.safety_manager.register_shutdown_callback(violation_callback)
        
        # Simulate violation
        self.audit_logger.log_safety_violation(
            violation_type="resource_limit_exceeded",
            description="CPU usage exceeded 95%"
        )
        
        # Trigger emergency shutdown
        self.safety_manager.emergency_shutdown("Resource violation")
        
        self.assertTrue(violation_detected)
        self.assertTrue(self.safety_manager.emergency_shutdown_triggered)

def run_safety_tests():
    """Run all safety system tests"""
    # Create test suite
    test_classes = [
        TestTargetValidator,
        TestResourceMonitor,
        TestEmergencyShutdown,
        TestEnvironmentDetector,
        TestAuditLogging,
        TestSafetyManager,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_safety_tests()
    sys.exit(0 if success else 1)