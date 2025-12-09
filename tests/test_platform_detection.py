"""
Unit tests for platform detection and abstraction system.
"""

import unittest
import platform
import socket
from unittest.mock import patch, MagicMock

from core.platform.detection import (
    PlatformDetector, PlatformType, Architecture, SystemInfo
)
from core.platform.abstraction import (
    PlatformEngine, WindowsAdapter, LinuxAdapter, MacOSAdapter
)


class TestPlatformDetector(unittest.TestCase):
    """Test platform detection functionality"""
    
    def test_detect_platform(self):
        """Test platform type detection"""
        detected_platform = PlatformDetector.detect_platform()
        self.assertIsInstance(detected_platform, PlatformType)
        
        # Should detect current platform correctly
        system = platform.system().lower()
        if system == "windows":
            self.assertEqual(detected_platform, PlatformType.WINDOWS)
        elif system == "linux":
            self.assertEqual(detected_platform, PlatformType.LINUX)
        elif system == "darwin":
            self.assertEqual(detected_platform, PlatformType.MACOS)
    
    def test_detect_architecture(self):
        """Test architecture detection"""
        detected_arch = PlatformDetector.detect_architecture()
        self.assertIsInstance(detected_arch, Architecture)
        
        # Should detect valid architecture
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            self.assertEqual(detected_arch, Architecture.X86_64)
        elif machine in ["arm64", "aarch64"]:
            self.assertEqual(detected_arch, Architecture.ARM64)
    
    def test_get_cpu_count(self):
        """Test CPU count detection"""
        cpu_count = PlatformDetector.get_cpu_count()
        self.assertIsInstance(cpu_count, int)
        self.assertGreater(cpu_count, 0)
    
    def test_get_memory_total(self):
        """Test memory detection"""
        memory_total = PlatformDetector.get_memory_total()
        self.assertIsInstance(memory_total, int)
        self.assertGreaterEqual(memory_total, 0)
    
    def test_has_admin_privileges(self):
        """Test privilege detection"""
        has_admin = PlatformDetector.has_admin_privileges()
        self.assertIsInstance(has_admin, bool)
    
    def test_supports_raw_sockets(self):
        """Test raw socket support detection"""
        supports_raw = PlatformDetector.supports_raw_sockets()
        self.assertIsInstance(supports_raw, bool)
    
    def test_get_network_interfaces(self):
        """Test network interface detection"""
        interfaces = PlatformDetector.get_network_interfaces()
        self.assertIsInstance(interfaces, list)
    
    def test_get_system_info(self):
        """Test comprehensive system info"""
        system_info = PlatformDetector.get_system_info()
        self.assertIsInstance(system_info, SystemInfo)
        
        # Validate key fields are populated
        self.assertIsInstance(system_info.platform_type, PlatformType)
        self.assertIsInstance(system_info.architecture, Architecture)


class TestPlatformAdapters(unittest.TestCase):
    """Test platform-specific adapters"""
    
    def test_linux_adapter_creation(self):
        """Test Linux adapter can be created"""
        adapter = LinuxAdapter()
        self.assertIsNotNone(adapter)
        
        # Test basic methods exist
        self.assertTrue(hasattr(adapter, 'get_buffer_sizes'))
        self.assertTrue(hasattr(adapter, 'get_optimal_socket_options'))
        self.assertTrue(hasattr(adapter, 'get_max_connections'))
    
    def test_windows_adapter_creation(self):
        """Test Windows adapter can be created"""
        adapter = WindowsAdapter()
        self.assertIsNotNone(adapter)
        
        # Test basic methods exist
        self.assertTrue(hasattr(adapter, 'get_buffer_sizes'))
        self.assertTrue(hasattr(adapter, 'get_optimal_socket_options'))
        self.assertTrue(hasattr(adapter, 'get_max_connections'))
    
    def test_macos_adapter_creation(self):
        """Test macOS adapter can be created"""
        adapter = MacOSAdapter()
        self.assertIsNotNone(adapter)
        
        # Test basic methods exist
        self.assertTrue(hasattr(adapter, 'get_buffer_sizes'))
        self.assertTrue(hasattr(adapter, 'get_optimal_socket_options'))
        self.assertTrue(hasattr(adapter, 'get_max_connections'))


class TestPlatformEngine(unittest.TestCase):
    """Test platform engine functionality"""
    
    def test_platform_engine_initialization(self):
        """Test platform engine initialization"""
        engine = PlatformEngine()
        self.assertIsNotNone(engine.system_info)
        self.assertIsNotNone(engine.adapter)
    
    def test_get_optimal_socket_config(self):
        """Test optimal socket configuration retrieval"""
        engine = PlatformEngine()
        
        tcp_config = engine.get_optimal_socket_config("TCP")
        self.assertIsNotNone(tcp_config)
        # Check for recv_buffer_size (actual attribute name)
        self.assertGreater(tcp_config.recv_buffer_size, 0)
        self.assertGreater(tcp_config.send_buffer_size, 0)
    
    def test_get_performance_settings(self):
        """Test performance settings retrieval"""
        engine = PlatformEngine()
        
        perf_settings = engine.get_max_performance_settings()
        self.assertIsNotNone(perf_settings)
        self.assertIsInstance(perf_settings, dict)
        self.assertIn('max_connections', perf_settings)
        self.assertGreater(perf_settings['max_connections'], 0)
    
    def test_network_capabilities(self):
        """Test network capabilities retrieval"""
        engine = PlatformEngine()
        
        capabilities = engine.get_network_capabilities()
        self.assertIsInstance(capabilities, dict)
        self.assertIn('raw_sockets', capabilities)
        self.assertIn('async_io', capabilities)
        self.assertIn('multiprocessing', capabilities)
    
    def test_get_system_info(self):
        """Test get_system_info method"""
        engine = PlatformEngine()
        
        system_info = engine.get_system_info()
        self.assertIsNotNone(system_info)
        self.assertTrue(hasattr(system_info, 'cpu_count'))
    
    def test_create_optimized_socket(self):
        """Test optimized socket creation"""
        engine = PlatformEngine()
        
        try:
            # Test TCP socket creation
            tcp_socket = engine.create_optimized_socket(socket.SOCK_STREAM)
            self.assertIsNotNone(tcp_socket)
            tcp_socket.close()
            
            # Test UDP socket creation
            udp_socket = engine.create_optimized_socket(socket.SOCK_DGRAM)
            self.assertIsNotNone(udp_socket)
            udp_socket.close()
            
        except (OSError, PermissionError):
            # Skip if we don't have permissions
            self.skipTest("Insufficient permissions for socket creation")


if __name__ == '__main__':
    unittest.main()
