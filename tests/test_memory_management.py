"""
Unit tests for advanced memory management system.
"""

import unittest
import threading
import time
import gc
from unittest.mock import patch, MagicMock

from core.memory.pool_manager import (
    MemoryPoolManager, PacketBufferPool, PacketBuffer, BufferSize
)
from core.memory.lockfree import (
    LockFreeQueue, LockFreeStack, LockFreeCounter, AtomicReference,
    LockFreeRingBuffer, LockFreeObjectPool
)
from core.memory.gc_optimizer import (
    GarbageCollectionOptimizer, GCMode, MemoryPressure, MemoryMonitor
)


class TestPacketBuffer(unittest.TestCase):
    """Test packet buffer functionality"""
    
    def test_buffer_creation(self):
        """Test packet buffer creation"""
        buffer = PacketBuffer(1024, 1)
        
        self.assertEqual(buffer.size, 1024)
        self.assertEqual(buffer.buffer_id, 1)
        self.assertGreater(buffer.creation_time, 0)
        self.assertFalse(buffer.is_locked)
        
        buffer.close()
    
    def test_buffer_operations(self):
        """Test buffer read/write operations"""
        buffer = PacketBuffer(1024, 1)
        
        # Test write
        test_data = b"Hello, World!"
        bytes_written = buffer.write_data(test_data)
        self.assertEqual(bytes_written, len(test_data))
        
        # Test read
        read_data = buffer.read_data(len(test_data))
        self.assertEqual(read_data, test_data)
        
        # Test partial read
        partial_data = buffer.read_data(5)
        self.assertEqual(partial_data, test_data[:5])
        
        buffer.close()
    
    def test_buffer_clear(self):
        """Test buffer clearing"""
        buffer = PacketBuffer(1024, 1)
        
        # Write data
        test_data = b"Test data"
        buffer.write_data(test_data)
        
        # Clear buffer
        buffer.clear()
        
        # Verify cleared
        cleared_data = buffer.read_data(len(test_data))
        self.assertEqual(cleared_data, b'\x00' * len(test_data))
        
        buffer.close()
    
    def test_buffer_locking(self):
        """Test buffer locking mechanism"""
        buffer = PacketBuffer(1024, 1)
        
        # Lock buffer
        buffer.lock()
        self.assertTrue(buffer.is_locked)
        
        # Try to write to locked buffer (should raise exception)
        with self.assertRaises(RuntimeError):
            buffer.write_data(b"test")
        
        # Unlock buffer
        buffer.unlock()
        self.assertFalse(buffer.is_locked)
        
        # Should be able to write now
        buffer.write_data(b"test")
        
        buffer.close()
    
    def test_buffer_metrics(self):
        """Test buffer usage metrics"""
        buffer = PacketBuffer(1024, 1)
        
        initial_use_count = buffer.use_count
        
        # Access buffer
        memview = buffer.get_buffer()
        self.assertIsNotNone(memview)
        self.assertGreater(buffer.use_count, initial_use_count)
        
        # Check age and idle time
        self.assertGreaterEqual(buffer.age, 0)
        self.assertGreaterEqual(buffer.idle_time, 0)
        
        buffer.close()


class TestPacketBufferPool(unittest.TestCase):
    """Test packet buffer pool functionality"""
    
    def test_pool_creation(self):
        """Test buffer pool creation"""
        pool = PacketBufferPool(1024, initial_count=5, max_count=10)
        
        self.assertEqual(pool.buffer_size, 1024)
        self.assertGreaterEqual(pool.available_count, 0)
        self.assertGreaterEqual(pool.allocated_count, 0)
        
        pool.close_all()
    
    def test_buffer_get_return(self):
        """Test getting and returning buffers"""
        pool = PacketBufferPool(1024, initial_count=3, max_count=5)
        
        # Get buffer
        buffer = pool.get_buffer()
        self.assertIsNotNone(buffer)
        self.assertEqual(buffer.size, 1024)
        
        # Return buffer
        pool.return_buffer(buffer)
        
        # Get another buffer (should reuse)
        buffer2 = pool.get_buffer()
        self.assertIsNotNone(buffer2)
        
        pool.close_all()
    
    def test_pool_statistics(self):
        """Test pool statistics collection"""
        pool = PacketBufferPool(1024, initial_count=2, max_count=5)
        
        # Get initial stats
        stats = pool.get_statistics()
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.total_allocated, 0)
        
        # Get and return buffer
        buffer = pool.get_buffer()
        if buffer:
            pool.return_buffer(buffer)
        
        # Check updated stats
        updated_stats = pool.get_statistics()
        self.assertGreaterEqual(updated_stats.total_allocated, stats.total_allocated)
        
        pool.close_all()
    
    def test_pool_cleanup(self):
        """Test pool cleanup of old buffers"""
        pool = PacketBufferPool(1024, initial_count=3, max_count=5)
        
        # Get some buffers and return them
        buffers = []
        for _ in range(3):
            buffer = pool.get_buffer()
            if buffer:
                buffers.append(buffer)
        
        for buffer in buffers:
            pool.return_buffer(buffer)
        
        # Cleanup old buffers (with very short max age for testing)
        pool.cleanup_old_buffers(max_idle_time=0.001)
        
        pool.close_all()


class TestMemoryPoolManager(unittest.TestCase):
    """Test memory pool manager functionality"""
    
    def test_manager_creation(self):
        """Test memory pool manager creation"""
        manager = MemoryPoolManager()
        self.assertIsNotNone(manager)
        
        # Check that pools are created
        stats = manager.get_comprehensive_statistics()
        self.assertIn('pools', stats)
        self.assertIn('global', stats)
        
        manager.cleanup()
    
    def test_buffer_allocation_by_size(self):
        """Test buffer allocation by size"""
        manager = MemoryPoolManager()
        
        # Test standard sizes
        buffer_1k = manager.get_buffer(1024)
        self.assertIsNotNone(buffer_1k)
        self.assertGreaterEqual(buffer_1k.size, 1024)
        
        buffer_large = manager.get_buffer(1472)  # Ethernet MTU
        self.assertIsNotNone(buffer_large)
        self.assertGreaterEqual(buffer_large.size, 1472)
        
        # Return buffers
        manager.return_buffer(buffer_1k)
        manager.return_buffer(buffer_large)
        
        manager.cleanup()
    
    def test_buffer_allocation_by_type(self):
        """Test buffer allocation by predefined types"""
        manager = MemoryPoolManager()
        
        # Test different buffer types
        packet_buffer = manager.get_packet_buffer()
        self.assertIsNotNone(packet_buffer)
        
        small_buffer = manager.get_small_buffer()
        self.assertIsNotNone(small_buffer)
        
        large_buffer = manager.get_large_buffer()
        self.assertIsNotNone(large_buffer)
        
        # Return buffers
        if packet_buffer:
            manager.return_buffer(packet_buffer)
        if small_buffer:
            manager.return_buffer(small_buffer)
        if large_buffer:
            manager.return_buffer(large_buffer)
        
        manager.cleanup()
    
    def test_custom_size_allocation(self):
        """Test allocation of custom-sized buffers"""
        manager = MemoryPoolManager()
        
        # Test custom size that doesn't match standard pools
        custom_buffer = manager.get_buffer(3333)
        self.assertIsNotNone(custom_buffer)
        self.assertGreaterEqual(custom_buffer.size, 3333)
        
        manager.return_buffer(custom_buffer)
        manager.cleanup()
    
    def test_manager_statistics(self):
        """Test comprehensive statistics collection"""
        manager = MemoryPoolManager()
        
        # Get some buffers
        buffers = []
        for size in [256, 1024, 1472]:
            buffer = manager.get_buffer(size)
            if buffer:
                buffers.append(buffer)
        
        # Get statistics
        stats = manager.get_comprehensive_statistics()
        self.assertIn('global', stats)
        self.assertIn('pools', stats)
        self.assertIn('summary', stats)
        
        # Check global stats
        global_stats = stats['global']
        self.assertIn('total_hits', global_stats)
        self.assertIn('total_misses', global_stats)
        
        # Return buffers
        for buffer in buffers:
            manager.return_buffer(buffer)
        
        manager.cleanup()


class TestLockFreeDataStructures(unittest.TestCase):
    """Test lock-free data structures"""
    
    def test_atomic_reference(self):
        """Test atomic reference operations"""
        ref = AtomicReference("initial")
        
        # Test get/set
        self.assertEqual(ref.get(), "initial")
        ref.set("updated")
        self.assertEqual(ref.get(), "updated")
        
        # Test compare and set
        success = ref.compare_and_set("updated", "final")
        self.assertTrue(success)
        self.assertEqual(ref.get(), "final")
        
        # Test failed compare and set
        success = ref.compare_and_set("wrong", "failed")
        self.assertFalse(success)
        self.assertEqual(ref.get(), "final")
    
    def test_lockfree_counter(self):
        """Test lock-free counter operations"""
        counter = LockFreeCounter(0)
        
        # Test increment
        new_value = counter.increment()
        self.assertEqual(new_value, 1)
        self.assertEqual(counter.value, 1)
        
        # Test decrement
        new_value = counter.decrement()
        self.assertEqual(new_value, 0)
        self.assertEqual(counter.value, 0)
        
        # Test add
        new_value = counter.add(5)
        self.assertEqual(new_value, 5)
        
        # Test get and increment
        old_value = counter.get_and_increment()
        self.assertEqual(old_value, 5)
        self.assertEqual(counter.value, 6)
    
    def test_lockfree_queue(self):
        """Test lock-free queue operations"""
        queue = LockFreeQueue()
        
        # Test empty queue
        self.assertTrue(queue.is_empty())
        self.assertIsNone(queue.dequeue())
        
        # Test enqueue/dequeue
        queue.enqueue("item1")
        queue.enqueue("item2")
        self.assertFalse(queue.is_empty())
        
        item = queue.dequeue()
        self.assertEqual(item, "item1")
        
        item = queue.dequeue()
        self.assertEqual(item, "item2")
        
        self.assertTrue(queue.is_empty())
    
    def test_lockfree_stack(self):
        """Test lock-free stack operations"""
        stack = LockFreeStack()
        
        # Test empty stack
        self.assertTrue(stack.is_empty())
        self.assertIsNone(stack.pop())
        
        # Test push/pop
        stack.push("item1")
        stack.push("item2")
        self.assertFalse(stack.is_empty())
        
        item = stack.pop()
        self.assertEqual(item, "item2")  # LIFO order
        
        item = stack.pop()
        self.assertEqual(item, "item1")
        
        self.assertTrue(stack.is_empty())
    
    def test_lockfree_ring_buffer(self):
        """Test lock-free ring buffer operations"""
        buffer = LockFreeRingBuffer(4)  # Power of 2
        
        # Test empty buffer
        self.assertTrue(buffer.is_empty())
        self.assertFalse(buffer.is_full())
        
        # Test put/get
        success = buffer.put("item1")
        self.assertTrue(success)
        self.assertFalse(buffer.is_empty())
        
        item = buffer.get()
        self.assertEqual(item, "item1")
        self.assertTrue(buffer.is_empty())
        
        # Test buffer full
        for i in range(3):  # Fill buffer (capacity - 1)
            buffer.put(f"item{i}")
        
        self.assertTrue(buffer.is_full())
        success = buffer.put("overflow")
        self.assertFalse(success)  # Should fail when full
    
    def test_lockfree_object_pool(self):
        """Test lock-free object pool"""
        def create_object():
            return {"data": "test", "reset_called": False}
        
        def reset_object(obj):
            obj["reset_called"] = True
        
        pool = LockFreeObjectPool(create_object, max_size=3)
        
        # Test borrow/return
        obj1 = pool.borrow()
        self.assertIsNotNone(obj1)
        
        # Add reset method to object
        obj1["reset"] = lambda: reset_object(obj1)
        
        success = pool.return_object(obj1)
        self.assertTrue(success)
        
        # Borrow again (should reuse)
        obj2 = pool.borrow()
        self.assertIsNotNone(obj2)
        
        # Check statistics
        stats = pool.get_statistics()
        self.assertIn('total_created', stats)
        self.assertIn('total_borrowed', stats)


class TestLockFreeConcurrency(unittest.TestCase):
    """Test lock-free data structures under concurrent access"""
    
    def test_concurrent_counter_access(self):
        """Test concurrent counter operations"""
        counter = LockFreeCounter(0)
        errors = []
        
        def worker():
            try:
                for _ in range(100):
                    counter.increment()
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors}")
        self.assertEqual(counter.value, 500)  # 5 threads * 100 increments
    
    def test_concurrent_queue_access(self):
        """Test concurrent queue operations"""
        queue = LockFreeQueue()
        items_produced = []
        items_consumed = []
        errors = []
        
        def producer():
            try:
                for i in range(50):
                    item = f"item_{threading.current_thread().ident}_{i}"
                    queue.enqueue(item)
                    items_produced.append(item)
            except Exception as e:
                errors.append(e)
        
        def consumer():
            try:
                for _ in range(50):
                    item = queue.dequeue()
                    if item:
                        items_consumed.append(item)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start producer and consumer threads
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)
        
        producer_thread.start()
        consumer_thread.start()
        
        producer_thread.join()
        consumer_thread.join()
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent errors: {errors}")
        self.assertGreater(len(items_consumed), 0)


class TestGarbageCollectionOptimizer(unittest.TestCase):
    """Test garbage collection optimizer"""
    
    def test_memory_monitor(self):
        """Test memory monitoring functionality"""
        monitor = MemoryMonitor(update_interval=0.1)
        
        # Start monitoring
        monitor.start()
        time.sleep(0.2)  # Let it collect some data
        
        # Get stats
        stats = monitor.get_stats()
        self.assertIsNotNone(stats)
        self.assertGreater(stats.total_memory_mb, 0)
        self.assertGreaterEqual(stats.memory_percent, 0)
        
        # Get memory pressure
        pressure = monitor.get_memory_pressure()
        self.assertIsInstance(pressure, MemoryPressure)
        
        monitor.stop()
    
    def test_gc_optimizer_creation(self):
        """Test GC optimizer creation and basic operations"""
        optimizer = GarbageCollectionOptimizer(
            gc_mode=GCMode.MANUAL,
            memory_check_interval=0.1,
            leak_detection_enabled=False
        )
        
        # Test force cleanup
        collected = optimizer.force_cleanup()
        self.assertIsInstance(collected, int)
        
        # Test statistics
        stats = optimizer.get_comprehensive_statistics()
        self.assertIn('memory', stats)
        self.assertIn('gc', stats)
        self.assertIn('optimizer', stats)
        
        optimizer.stop()
    
    def test_gc_optimizer_context_manager(self):
        """Test GC optimizer as context manager"""
        with GarbageCollectionOptimizer(gc_mode=GCMode.ADAPTIVE) as optimizer:
            # Test that optimizer is running
            stats = optimizer.get_comprehensive_statistics()
            self.assertTrue(stats['optimizer']['running'])
        
        # Should be stopped after context exit
    
    def test_gc_recommendations(self):
        """Test memory optimization recommendations"""
        optimizer = GarbageCollectionOptimizer(
            gc_mode=GCMode.ADAPTIVE,
            leak_detection_enabled=False
        )
        
        recommendations = optimizer.get_memory_recommendations()
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        optimizer.stop()
    
    def test_gc_mode_switching(self):
        """Test switching between GC modes"""
        optimizer = GarbageCollectionOptimizer(gc_mode=GCMode.AUTOMATIC)
        
        # Test performance optimization
        optimizer.optimize_for_performance()
        
        # Test memory optimization
        optimizer.optimize_for_memory()
        
        optimizer.stop()


class TestMemoryConcurrency(unittest.TestCase):
    """Test memory management under concurrent access"""
    
    def test_concurrent_pool_access(self):
        """Test concurrent memory pool access"""
        manager = MemoryPoolManager()
        buffers = []
        errors = []
        
        def worker():
            try:
                for _ in range(20):
                    buffer = manager.get_packet_buffer()
                    if buffer:
                        buffers.append(buffer)
                        time.sleep(0.001)
                        manager.return_buffer(buffer)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        
        manager.cleanup()


if __name__ == '__main__':
    unittest.main()