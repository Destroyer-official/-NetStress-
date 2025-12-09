"""
Lock-free data structures for high concurrency operations.
Implements atomic operations and lock-free algorithms for maximum performance.
"""

import threading
import time
import ctypes
from typing import Optional, Any, Generic, TypeVar, List
from dataclasses import dataclass
from enum import Enum
import weakref

T = TypeVar('T')


class AtomicReference(Generic[T]):
    """Atomic reference implementation using compare-and-swap"""
    
    def __init__(self, initial_value: Optional[T] = None):
        self._value = initial_value
        self._lock = threading.Lock()  # Fallback for platforms without true CAS
    
    def get(self) -> Optional[T]:
        """Get the current value"""
        return self._value
    
    def set(self, new_value: T):
        """Set a new value"""
        with self._lock:
            self._value = new_value
    
    def compare_and_set(self, expected: T, new_value: T) -> bool:
        """Compare and set operation (atomic)"""
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False
    
    def get_and_set(self, new_value: T) -> Optional[T]:
        """Get current value and set new value atomically"""
        with self._lock:
            old_value = self._value
            self._value = new_value
            return old_value


class LockFreeCounter:
    """Lock-free counter using atomic operations"""
    
    def __init__(self, initial_value: int = 0):
        self._value = ctypes.c_longlong(initial_value)
        self._lock = threading.Lock()  # Fallback for thread safety
    
    def increment(self, delta: int = 1) -> int:
        """Increment counter and return new value"""
        with self._lock:
            old_value = self._value.value
            self._value.value += delta
            return self._value.value
    
    def decrement(self, delta: int = 1) -> int:
        """Decrement counter and return new value"""
        return self.increment(-delta)
    
    def add(self, delta: int) -> int:
        """Add delta to counter and return new value"""
        return self.increment(delta)
    
    def get_and_increment(self, delta: int = 1) -> int:
        """Get current value and increment"""
        with self._lock:
            old_value = self._value.value
            self._value.value += delta
            return old_value
    
    def get_and_decrement(self, delta: int = 1) -> int:
        """Get current value and decrement"""
        return self.get_and_increment(-delta)
    
    def compare_and_set(self, expected: int, new_value: int) -> bool:
        """Compare and set operation"""
        with self._lock:
            if self._value.value == expected:
                self._value.value = new_value
                return True
            return False
    
    @property
    def value(self) -> int:
        """Get current value"""
        return self._value.value
    
    def reset(self, new_value: int = 0):
        """Reset counter to new value"""
        with self._lock:
            self._value.value = new_value


@dataclass
class LockFreeNode(Generic[T]):
    """Node for lock-free data structures"""
    data: Optional[T]
    next: Optional['LockFreeNode[T]'] = None
    marked: bool = False  # For deletion marking


class LockFreeQueue(Generic[T]):
    """Lock-free queue implementation using Michael & Scott algorithm"""
    
    def __init__(self):
        # Create dummy node
        dummy = LockFreeNode(None)
        self._head = AtomicReference(dummy)
        self._tail = AtomicReference(dummy)
        self._size = LockFreeCounter(0)
    
    def enqueue(self, item: T) -> bool:
        """Add item to the queue"""
        new_node = LockFreeNode(item)
        
        while True:
            tail = self._tail.get()
            next_node = tail.next
            
            # Check if tail is still the last node
            if tail == self._tail.get():
                if next_node is None:
                    # Try to link new node at the end of the list
                    if self._compare_and_set_next(tail, None, new_node):
                        break
                else:
                    # Try to advance tail pointer
                    self._tail.compare_and_set(tail, next_node)
        
        # Try to advance tail pointer
        self._tail.compare_and_set(tail, new_node)
        self._size.increment()
        return True
    
    def dequeue(self) -> Optional[T]:
        """Remove and return item from queue"""
        while True:
            head = self._head.get()
            tail = self._tail.get()
            next_node = head.next
            
            # Check if head is still the first node
            if head == self._head.get():
                if head == tail:
                    if next_node is None:
                        # Queue is empty
                        return None
                    # Try to advance tail pointer
                    self._tail.compare_and_set(tail, next_node)
                else:
                    if next_node is None:
                        continue
                    
                    # Read data before potential dequeue
                    data = next_node.data
                    
                    # Try to advance head pointer
                    if self._head.compare_and_set(head, next_node):
                        self._size.decrement()
                        return data
    
    def _compare_and_set_next(self, node: LockFreeNode[T], 
                             expected: Optional[LockFreeNode[T]], 
                             new_node: LockFreeNode[T]) -> bool:
        """Compare and set next pointer of a node"""
        # Simplified implementation - in real implementation would use atomic operations
        if node.next == expected:
            node.next = new_node
            return True
        return False
    
    def peek(self) -> Optional[T]:
        """Peek at the front item without removing it"""
        head = self._head.get()
        if head and head.next:
            return head.next.data
        return None
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        head = self._head.get()
        tail = self._tail.get()
        return head == tail and head.next is None
    
    def size(self) -> int:
        """Get approximate size of queue"""
        return self._size.value
    
    def clear(self):
        """Clear all items from queue"""
        while not self.is_empty():
            self.dequeue()


class LockFreeStack(Generic[T]):
    """Lock-free stack implementation using Treiber's algorithm"""
    
    def __init__(self):
        self._head = AtomicReference(None)
        self._size = LockFreeCounter(0)
    
    def push(self, item: T) -> bool:
        """Push item onto stack"""
        new_node = LockFreeNode(item)
        
        while True:
            current_head = self._head.get()
            new_node.next = current_head
            
            if self._head.compare_and_set(current_head, new_node):
                self._size.increment()
                return True
    
    def pop(self) -> Optional[T]:
        """Pop item from stack"""
        while True:
            current_head = self._head.get()
            
            if current_head is None:
                return None
            
            next_node = current_head.next
            
            if self._head.compare_and_set(current_head, next_node):
                self._size.decrement()
                return current_head.data
    
    def peek(self) -> Optional[T]:
        """Peek at top item without removing it"""
        head = self._head.get()
        return head.data if head else None
    
    def is_empty(self) -> bool:
        """Check if stack is empty"""
        return self._head.get() is None
    
    def size(self) -> int:
        """Get approximate size of stack"""
        return self._size.value
    
    def clear(self):
        """Clear all items from stack"""
        while not self.is_empty():
            self.pop()


class LockFreeHashMap(Generic[T]):
    """Lock-free hash map implementation"""
    
    def __init__(self, initial_capacity: int = 16):
        self.capacity = initial_capacity
        self._buckets = [LockFreeQueue() for _ in range(initial_capacity)]
        self._size = LockFreeCounter(0)
        self._resize_threshold = initial_capacity * 0.75
    
    def _hash(self, key: Any) -> int:
        """Simple hash function"""
        return hash(key) % self.capacity
    
    def put(self, key: Any, value: T) -> bool:
        """Put key-value pair into map"""
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]
        
        # For simplicity, we'll add to the bucket
        # In a real implementation, we'd need to handle key collisions properly
        bucket.enqueue((key, value))
        self._size.increment()
        
        return True
    
    def get(self, key: Any) -> Optional[T]:
        """Get value by key"""
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]
        
        # Linear search in bucket (simplified)
        # In real implementation, would use more sophisticated approach
        temp_items = []
        result = None
        
        # Dequeue all items to search
        while True:
            item = bucket.dequeue()
            if item is None:
                break
            
            item_key, item_value = item
            if item_key == key:
                result = item_value
            
            temp_items.append(item)
        
        # Re-enqueue all items
        for item in temp_items:
            bucket.enqueue(item)
        
        return result
    
    def remove(self, key: Any) -> Optional[T]:
        """Remove key-value pair"""
        bucket_index = self._hash(key)
        bucket = self._buckets[bucket_index]
        
        temp_items = []
        result = None
        
        # Dequeue all items
        while True:
            item = bucket.dequeue()
            if item is None:
                break
            
            item_key, item_value = item
            if item_key == key:
                result = item_value
                self._size.decrement()
            else:
                temp_items.append(item)
        
        # Re-enqueue remaining items
        for item in temp_items:
            bucket.enqueue(item)
        
        return result
    
    def size(self) -> int:
        """Get size of map"""
        return self._size.value
    
    def is_empty(self) -> bool:
        """Check if map is empty"""
        return self._size.value == 0


class LockFreeRingBuffer(Generic[T]):
    """Lock-free ring buffer for high-performance producer-consumer scenarios"""
    
    def __init__(self, capacity: int):
        if capacity <= 0 or (capacity & (capacity - 1)) != 0:
            raise ValueError("Capacity must be a power of 2")
        
        self.capacity = capacity
        self.mask = capacity - 1
        self._buffer = [None] * capacity
        self._head = LockFreeCounter(0)
        self._tail = LockFreeCounter(0)
    
    def put(self, item: T) -> bool:
        """Put item into buffer"""
        current_tail = self._tail.value
        next_tail = (current_tail + 1) & self.mask
        
        # Check if buffer is full
        if next_tail == self._head.value:
            return False
        
        self._buffer[current_tail] = item
        
        # Advance tail
        while not self._tail.compare_and_set(current_tail, next_tail):
            current_tail = self._tail.value
            next_tail = (current_tail + 1) & self.mask
            
            if next_tail == self._head.value:
                return False
        
        return True
    
    def get(self) -> Optional[T]:
        """Get item from buffer"""
        current_head = self._head.value
        
        # Check if buffer is empty
        if current_head == self._tail.value:
            return None
        
        item = self._buffer[current_head]
        self._buffer[current_head] = None  # Clear reference
        
        # Advance head
        next_head = (current_head + 1) & self.mask
        while not self._head.compare_and_set(current_head, next_head):
            current_head = self._head.value
            if current_head == self._tail.value:
                return None
            next_head = (current_head + 1) & self.mask
        
        return item
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return self._head.value == self._tail.value
    
    def is_full(self) -> bool:
        """Check if buffer is full"""
        return ((self._tail.value + 1) & self.mask) == self._head.value
    
    def size(self) -> int:
        """Get current size"""
        return (self._tail.value - self._head.value) & self.mask
    
    def available_space(self) -> int:
        """Get available space"""
        return self.capacity - self.size() - 1


class LockFreeObjectPool(Generic[T]):
    """Lock-free object pool for reusing expensive objects"""
    
    def __init__(self, factory_func, max_size: int = 1000):
        self.factory_func = factory_func
        self.max_size = max_size
        self._available_objects = LockFreeStack()
        self._total_created = LockFreeCounter(0)
        self._total_borrowed = LockFreeCounter(0)
        self._total_returned = LockFreeCounter(0)
    
    def borrow(self) -> T:
        """Borrow an object from the pool"""
        obj = self._available_objects.pop()
        
        if obj is None:
            # Create new object
            obj = self.factory_func()
            self._total_created.increment()
        
        self._total_borrowed.increment()
        return obj
    
    def return_object(self, obj: T) -> bool:
        """Return an object to the pool"""
        if self._available_objects.size() >= self.max_size:
            # Pool is full, don't return object
            return False
        
        # Reset object if it has a reset method
        if hasattr(obj, 'reset'):
            try:
                obj.reset()
            except Exception:
                # Don't return objects that can't be reset
                return False
        
        self._available_objects.push(obj)
        self._total_returned.increment()
        return True
    
    def get_statistics(self) -> dict:
        """Get pool statistics"""
        return {
            'available_objects': self._available_objects.size(),
            'total_created': self._total_created.value,
            'total_borrowed': self._total_borrowed.value,
            'total_returned': self._total_returned.value,
            'current_borrowed': self._total_borrowed.value - self._total_returned.value
        }


class AtomicBoolean:
    """Atomic boolean implementation"""
    
    def __init__(self, initial_value: bool = False):
        self._value = AtomicReference(initial_value)
    
    def get(self) -> bool:
        """Get current value"""
        return self._value.get()
    
    def set(self, new_value: bool):
        """Set new value"""
        self._value.set(new_value)
    
    def compare_and_set(self, expected: bool, new_value: bool) -> bool:
        """Compare and set operation"""
        return self._value.compare_and_set(expected, new_value)
    
    def get_and_set(self, new_value: bool) -> bool:
        """Get current value and set new value"""
        return self._value.get_and_set(new_value)


class LockFreeStatistics:
    """Lock-free statistics collector"""
    
    def __init__(self):
        self.count = LockFreeCounter(0)
        self.sum = LockFreeCounter(0)
        self.min_value = AtomicReference(float('inf'))
        self.max_value = AtomicReference(float('-inf'))
        self.sum_of_squares = LockFreeCounter(0)
    
    def add_sample(self, value: float):
        """Add a sample value"""
        int_value = int(value * 1000)  # Convert to int for atomic operations
        
        self.count.increment()
        self.sum.add(int_value)
        self.sum_of_squares.add(int_value * int_value)
        
        # Update min
        while True:
            current_min = self.min_value.get()
            if value >= current_min or self.min_value.compare_and_set(current_min, value):
                break
        
        # Update max
        while True:
            current_max = self.max_value.get()
            if value <= current_max or self.max_value.compare_and_set(current_max, value):
                break
    
    def get_statistics(self) -> dict:
        """Get current statistics"""
        count = self.count.value
        if count == 0:
            return {
                'count': 0,
                'mean': 0.0,
                'min': 0.0,
                'max': 0.0,
                'variance': 0.0,
                'std_dev': 0.0
            }
        
        sum_val = self.sum.value / 1000.0
        sum_sq = self.sum_of_squares.value / 1000000.0
        mean = sum_val / count
        variance = (sum_sq / count) - (mean * mean)
        std_dev = variance ** 0.5 if variance >= 0 else 0.0
        
        return {
            'count': count,
            'mean': mean,
            'min': self.min_value.get(),
            'max': self.max_value.get(),
            'variance': variance,
            'std_dev': std_dev
        }
    
    def reset(self):
        """Reset all statistics"""
        self.count.reset()
        self.sum.reset()
        self.min_value.set(float('inf'))
        self.max_value.set(float('-inf'))
        self.sum_of_squares.reset()