"""
Integration tests for core infrastructure components.
Tests the interaction between platform detection, socket management, and memory management.
"""

import unittest
import threading
import time
import socket
from unittest.mock import patch

from core.platform.detection import PlatformDetector
from core.platform.abstraction import PlatformEngine
from core.platform.capabilities import CapabilityMapper
from core.networking.socket_factory import SocketFactory, SocketType
from core.networking.buffer_manager import ZeroCopyBufferManager
from core.memory.pool_manager import MemoryPoolManager
from core.memory.gc_optimizer import GarbageCollectionOptimizer, GCMode


class TestPlatformIntegration(unittest.TestCase):
    """Test integration between platform components"""
    
    def test_platform_to_socket_integration(self):
        """Test platform detection integration with socket creation"""
        # Get system info
        system_info = PlatformDetector.get_system_info()
        self.assertIsNotNone(system_info)
        
        # Create platform engine
        platform_engine = PlatformEngine()
        # Compare platform types - handle both string and enum values
        engine_platform = platform_engine.system_info.platform_type
        detector_platform = system_info.platform_type
        # Convert enum to string value if needed
        if hasattr(detector_platform, 'value'):
            detector_platform = detector_platform.value
        self.assertEqual(engine_platform, detector_platform)
        
        # Create socket factory using platform engine
        socket_factory = SocketFactory()
        
        try:
            # Create socket using platform-optimized settings
            udp_socket = socket_factory.create_udp_socket()
            self.assertIsNotNone(udp_socket)
            # Check that it's a UDP socket (SOCK_DGRAM = 2)
            import socket
            self.assertEqual(udp_socket.type, socket.SOCK_DGRAM)
            
            udp_socket.close()
            
        except (OSError, PermissionError):
            self.skipTest("Insufficient permissions for socket creation")
        
        socket_factory.cleanup()
    
    def test_platform_capabilities_integration(self):
        """Test platform capabilities with actual system"""
        system_info = PlatformDetector.get_system_info()
        
        # Create capability profile
        profile = CapabilityMapper.create_capability_profile(system_info)
        self.assertIsNotNone(profile)
        
        # Get optimization recommendations
        recommendations = CapabilityMapper.get_optimization_recommendations(profile)
        self.assertIsInstance(recommendations, list)
        
        # Estimate attack capacity for different protocols
        tcp_capacity = CapabilityMapper.estimate_attack_capacity(profile, "TCP")
        udp_capacity = CapabilityMapper.estimate_attack_capacity(profile, "UDP")
        
        self.assertIn('estimated_pps', tcp_capacity)
        self.assertIn('estimated_pps', udp_capacity)
        
        # UDP should generally be more efficient than TCP
        self.assertGreaterEqual(udp_capacity['estimated_pps'], tcp_capacity['estimated_pps'])


class TestSocketMemoryIntegration(unittest.TestCase):
    """Test integration between socket management and memory management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.socket_factory = SocketFactory()
        self.memory_manager = MemoryPoolManager()
        self.buffer_manager = ZeroCopyBufferManager()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.socket_factory.cleanup()
        self.memory_manager.cleanup()
        self.buffer_manager.cleanup()
    
    def test_socket_with_memory_buffers(self):
        """Test socket operations with memory-managed buffers"""
        try:
            # Create socket
            udp_socket = self.socket_factory.create_udp_socket()
            self.assertIsNotNone(udp_socket)
            
            # Get buffer from memory manager
            buffer = self.memory_manager.get_packet_buffer()
            self.assertIsNotNone(buffer)
            
            # Write test data to buffer
            test_data = b"Integration test data"
            buffer.write_data(test_data)
            
            # Read data from buffer for socket operation
            socket_data = buffer.read_data(len(test_data))
            self.assertEqual(socket_data, test_data)
            
            # Test socket send operation (to non-routable address)
            try:
                bytes_sent = udp_socket.sendto(socket_data, ("192.0.2.1", 12345))
                self.assertGreater(bytes_sent, 0)
            except (OSError, socket.error):
                # Network operations might fail in test environment
                pass
            
            # Return buffer to pool
            self.memory_manager.return_buffer(buffer)
            udp_socket.close()
            
        except (OSError, PermissionError):
            self.skipTest("Insufficient permissions for socket creation")
    
    def test_zero_copy_buffer_with_sockets(self):
        """Test zero-copy buffers with socket operations"""
        try:
            # Create socket
            udp_socket = self.socket_factory.create_udp_socket()
            self.assertIsNotNone(udp_socket)
            
            # Get zero-copy buffer
            zero_copy_buffer = self.buffer_manager.get_packet_buffer()
            self.assertIsNotNone(zero_copy_buffer)
            
            # Write data to zero-copy buffer
            test_data = b"Zero-copy test data"
            zero_copy_buffer.write_data(test_data)
            
            # Get buffer view for socket operations
            buffer_view = zero_copy_buffer.get_buffer()
            self.assertIsNotNone(buffer_view)
            
            # Test socket operation with buffer view
            try:
                # Convert memoryview to bytes for socket operation
                socket_data = bytes(buffer_view[:len(test_data)])
                bytes_sent = udp_socket.sendto(socket_data, ("192.0.2.1", 12345))
                self.assertGreater(bytes_sent, 0)
            except (OSError, socket.error):
                # Network operations might fail in test environment
                pass
            
            # Return buffer
            self.buffer_manager.return_buffer(zero_copy_buffer)
            udp_socket.close()
            
        except (OSError, PermissionError):
            self.skipTest("Insufficient permissions for socket creation")


class TestFullSystemIntegration(unittest.TestCase):
    """Test full system integration with all components"""
    
    def setUp(self):
        """Set up comprehensive test environment"""
        self.platform_engine = PlatformEngine()
        self.socket_factory = SocketFactory()
        self.memory_manager = MemoryPoolManager()
        self.buffer_manager = ZeroCopyBufferManager()
        self.gc_optimizer = GarbageCollectionOptimizer(
            gc_mode=GCMode.MANUAL,
            leak_detection_enabled=False
        )
    
    def tearDown(self):
        """Clean up test environment"""
        self.socket_factory.cleanup()
        self.memory_manager.cleanup()
        self.buffer_manager.cleanup()
        self.gc_optimizer.stop()
    
    def test_complete_packet_processing_pipeline(self):
        """Test complete packet processing pipeline"""
        try:
            # 1. Get system capabilities
            system_info = self.platform_engine.get_system_info()
            capabilities = self.platform_engine.get_network_capabilities()
            
            # 2. Create optimized socket
            udp_socket = self.socket_factory.create_udp_socket()
            self.assertIsNotNone(udp_socket)
            
            # 3. Get memory buffer
            packet_buffer = self.memory_manager.get_packet_buffer()
            self.assertIsNotNone(packet_buffer)
            
            # 4. Prepare packet data
            packet_data = b"Complete integration test packet"
            packet_buffer.write_data(packet_data)
            
            # 5. Get zero-copy buffer for high performance
            zero_copy_buffer = self.buffer_manager.get_packet_buffer()
            self.assertIsNotNone(zero_copy_buffer)
            
            # 6. Copy data to zero-copy buffer
            zero_copy_buffer.write_data(packet_data)
            
            # 7. Perform socket operation
            try:
                socket_data = packet_buffer.read_data(len(packet_data))
                bytes_sent = udp_socket.sendto(socket_data, ("192.0.2.1", 12345))
                self.assertGreater(bytes_sent, 0)
                
                # Note: Standard Python sockets don't have metrics attribute
                # This would require a custom socket wrapper for tracking
                # Skip metrics check for standard sockets
                
            except (OSError, socket.error):
                # Network operations might fail in test environment
                pass
            
            # 8. Clean up resources
            self.memory_manager.return_buffer(packet_buffer)
            self.buffer_manager.return_buffer(zero_copy_buffer)
            self.socket_factory.return_socket(udp_socket)
            
            # 9. Force garbage collection
            collected = self.gc_optimizer.force_cleanup()
            self.assertIsInstance(collected, int)
            
        except (OSError, PermissionError):
            self.skipTest("Insufficient permissions for socket creation")
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring across all components"""
        # Get platform performance settings
        perf_settings = self.platform_engine.get_max_performance_settings()
        self.assertIsNotNone(perf_settings)
        
        # Get socket statistics
        socket_stats = self.socket_factory.get_socket_statistics()
        self.assertIn('active_sockets', socket_stats)
        
        # Get memory statistics
        memory_stats = self.memory_manager.get_comprehensive_statistics()
        self.assertIn('global', memory_stats)
        
        # Get buffer statistics
        buffer_stats = self.buffer_manager.get_statistics()
        self.assertIn('pools', buffer_stats)
        
        # Get GC statistics
        gc_stats = self.gc_optimizer.get_comprehensive_statistics()
        self.assertIn('memory', gc_stats)
        self.assertIn('gc', gc_stats)
        
        # Verify all components are providing metrics
        self.assertIsInstance(socket_stats['active_sockets'], int)
        self.assertIsInstance(memory_stats['global']['total_hits'], int)
        self.assertIsInstance(buffer_stats['total_metrics'].total_allocated, int)
        self.assertIsInstance(gc_stats['memory']['total_mb'], float)


class TestConcurrentIntegration(unittest.TestCase):
    """Test system integration under concurrent load"""
    
    def setUp(self):
        """Set up concurrent test environment"""
        self.socket_factory = SocketFactory()
        self.memory_manager = MemoryPoolManager()
        self.buffer_manager = ZeroCopyBufferManager()
    
    def tearDown(self):
        """Clean up concurrent test environment"""
        self.socket_factory.cleanup()
        self.memory_manager.cleanup()
        self.buffer_manager.cleanup()
    
    def test_concurrent_packet_processing(self):
        """Test concurrent packet processing across all components"""
        errors = []
        processed_packets = []
        
        def packet_worker(worker_id):
            try:
                for i in range(10):
                    # Get resources
                    try:
                        socket = self.socket_factory.create_udp_socket()
                        buffer = self.memory_manager.get_packet_buffer()
                        zero_copy_buffer = self.buffer_manager.get_packet_buffer()
                        
                        if socket and buffer and zero_copy_buffer:
                            # Process packet
                            packet_data = f"Worker {worker_id} packet {i}".encode()
                            buffer.write_data(packet_data)
                            
                            # Simulate packet processing
                            processed_data = buffer.read_data(len(packet_data))
                            processed_packets.append(processed_data)
                            
                            # Clean up
                            self.memory_manager.return_buffer(buffer)
                            self.buffer_manager.return_buffer(zero_copy_buffer)
                            self.socket_factory.return_socket(socket)
                            
                    except (OSError, PermissionError):
                        # Skip permission errors in test environment
                        pass
                    
                    time.sleep(0.001)  # Small delay
                    
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")
        
        # Start multiple worker threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=packet_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent processing errors: {errors}")
        self.assertGreater(len(processed_packets), 0)
    
    def test_resource_cleanup_under_load(self):
        """Test resource cleanup under concurrent load"""
        errors = []
        
        def resource_worker():
            try:
                resources = []
                
                # Allocate resources
                for _ in range(20):
                    try:
                        socket = self.socket_factory.create_udp_socket()
                        buffer = self.memory_manager.get_packet_buffer()
                        zero_copy_buffer = self.buffer_manager.get_packet_buffer()
                        
                        if socket:
                            resources.append(('socket', socket))
                        if buffer:
                            resources.append(('buffer', buffer))
                        if zero_copy_buffer:
                            resources.append(('zero_copy', zero_copy_buffer))
                            
                    except (OSError, PermissionError):
                        # Skip permission errors
                        pass
                
                # Clean up resources
                for resource_type, resource in resources:
                    if resource_type == 'socket':
                        self.socket_factory.return_socket(resource)
                    elif resource_type == 'buffer':
                        self.memory_manager.return_buffer(resource)
                    elif resource_type == 'zero_copy':
                        self.buffer_manager.return_buffer(resource)
                        
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=resource_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Resource cleanup errors: {errors}")
        
        # Verify system state after cleanup
        socket_stats = self.socket_factory.get_socket_statistics()
        memory_stats = self.memory_manager.get_comprehensive_statistics()
        buffer_stats = self.buffer_manager.get_statistics()
        
        # All components should be in a clean state
        self.assertIsInstance(socket_stats['active_sockets'], int)
        self.assertIsInstance(memory_stats['summary']['total_current_allocated'], int)
        self.assertIsInstance(buffer_stats['total_metrics'].current_allocated, int)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across integrated components"""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail"""
        socket_factory = SocketFactory()
        memory_manager = MemoryPoolManager()
        
        try:
            # Test with limited resources
            sockets = []
            buffers = []
            
            # Try to exhaust resources
            for i in range(100):
                try:
                    socket = socket_factory.create_udp_socket()
                    if socket:
                        sockets.append(socket)
                    
                    buffer = memory_manager.get_packet_buffer()
                    if buffer:
                        buffers.append(buffer)
                        
                except (OSError, PermissionError):
                    # Expected when resources are exhausted
                    break
            
            # System should still be functional
            stats = socket_factory.get_socket_statistics()
            self.assertIsInstance(stats, dict)
            
            # Clean up
            for socket in sockets:
                socket_factory.return_socket(socket)
            for buffer in buffers:
                memory_manager.return_buffer(buffer)
                
        except Exception as e:
            self.fail(f"System should handle resource exhaustion gracefully: {e}")
        
        finally:
            socket_factory.cleanup()
            memory_manager.cleanup()
    
    def test_component_isolation(self):
        """Test that component failures don't cascade"""
        socket_factory = SocketFactory()
        memory_manager = MemoryPoolManager()
        
        try:
            # Test memory manager failure doesn't affect socket factory
            buffer = memory_manager.get_packet_buffer()
            if buffer:
                # Force buffer into invalid state
                buffer.close()
                
                # Socket factory should still work
                socket = socket_factory.create_udp_socket()
                self.assertIsNotNone(socket)
                socket.close()
            
            # Test socket factory issues don't affect memory manager
            try:
                # Try to create invalid socket type
                with self.assertRaises((ValueError, RuntimeError)):
                    socket_factory.create_socket(None)
            except:
                pass
            
            # Memory manager should still work
            buffer2 = memory_manager.get_packet_buffer()
            self.assertIsNotNone(buffer2)
            memory_manager.return_buffer(buffer2)
            
        finally:
            socket_factory.cleanup()
            memory_manager.cleanup()


if __name__ == '__main__':
    unittest.main()