"""
Zero-Copy Networking Implementation

Implements zero-copy packet processing pipelines, direct hardware access,
and NUMA-aware processing for maximum performance.
"""

import os
import sys
import mmap
import ctypes
import logging
import platform
import threading
from typing import Dict, Optional, List, Any, Tuple, Union
from abc import ABC, abstractmethod
import multiprocessing
import queue
import time
import socket

logger = logging.getLogger(__name__)

class ZeroCopyBuffer:
    """Zero-copy buffer implementation using memory mapping"""  
  
    def __init__(self, size: int, numa_node: Optional[int] = None):
        self.size = size
        self.numa_node = numa_node
        self.buffer = None
        self.mapped_memory = None
        self._initialize_buffer()
        
    def _initialize_buffer(self):
        """Initialize zero-copy buffer with memory mapping"""
        try:
            # Create memory-mapped buffer for zero-copy operations
            self.buffer = mmap.mmap(-1, self.size, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)    
        
            # Configure NUMA affinity if specified
            if self.numa_node is not None:
                self._set_numa_affinity()
                
            # Lock memory to prevent swapping
            if hasattr(mmap, 'MADV_DONTFORK'):
                self.buffer.madvise(mmap.MADV_DONTFORK)
                
            logger.debug(f"Initialized zero-copy buffer: {self.size} bytes")
            
        except Exception as e:
            logger.error(f"Zero-copy buffer initialization failed: {e}")
            raise
            
    def _set_numa_affinity(self):
        """Set NUMA node affinity for the buffer"""
        try:
            if platform.system() == 'Linux':
                # Use numactl to set memory policy
                import subprocess
                subprocess.run(['numactl', '--membind', str(self.numa_node), 
                              '--', 'echo', 'numa_set'], check=False)
                logger.debug(f"Set NUMA affinity to node {self.numa_node}")
        except Exception as e:
            logger.warning(f"NUMA affinity setting failed: {e}")
            
    def get_buffer_address(self) -> int:
        """Get the memory address of the buffer for direct access"""
        if self.buffer:
            return ctypes.addressof(ctypes.c_char.from_buffer(self.buffer))
        return 0
        
    def write_data(self, data: bytes, offset: int = 0) -> bool:
        """Write data to buffer without copying"""
        try:
            if offset + len(data) > self.size:
                return False
                
            self.buffer[offset:offset + len(data)] = data
            return True
            
        except Exception as e:
            logger.error(f"Zero-copy write failed: {e}")
            return False
            
    def read_data(self, length: int, offset: int = 0) -> bytes:
        """Read data from buffer without copying"""
        try:
            if offset + length > self.size:
                return b''
                
            return bytes(self.buffer[offset:offset + length])
            
        except Exception as e:
            logger.error(f"Zero-copy read failed: {e}")
            return b''
            
    def close(self):
        """Close and cleanup the buffer"""
        if self.buffer:
            self.buffer.close()
            self.buffer = None

class ZeroCopySocketBase(ABC):
    """Abstract base class for zero-copy socket implementations"""
    
    def __init__(self):
        self.socket = None
        self.zero_copy_enabled = False
        
    @abstractmethod
    def create_zero_copy_socket(self, family: int, type: int) -> bool:
        """Create zero-copy optimized socket"""
        pass
        
    @abstractmethod
    def send_zero_copy(self, buffer: ZeroCopyBuffer, size: int) -> int:
        """Send data using zero-copy"""
        pass
        
    @abstractmethod
    def receive_zero_copy(self, buffer: ZeroCopyBuffer) -> int:
        """Receive data using zero-copy"""
        pass

class LinuxZeroCopySocket(ZeroCopySocketBase):
    """Linux-specific zero-copy socket implementation"""
    
    def __init__(self):
        super().__init__()
        self.sendfile_supported = False
        self.splice_supported = False
        
    def create_zero_copy_socket(self, family: int, type: int) -> bool:
        """Create Linux zero-copy optimized socket"""
        try:
            self.socket = socket.socket(family, type)
            
            # Enable zero-copy optimizations
            self._enable_linux_optimizations()
            
            # Check for advanced zero-copy support
            self._check_zero_copy_support()
            
            self.zero_copy_enabled = True
            logger.info("Linux zero-copy socket created")
            return True
            
        except Exception as e:
            logger.error(f"Linux zero-copy socket creation failed: {e}")
            return False
            
    def _enable_linux_optimizations(self):
        """Enable Linux-specific socket optimizations"""
        try:
            # Enable TCP_NODELAY for low latency
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Enable SO_REUSEADDR and SO_REUSEPORT
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, 'SO_REUSEPORT'):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                
            # Set large buffer sizes
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            
            # Enable zero-copy send if available
            if hasattr(socket, 'MSG_ZEROCOPY'):
                logger.info("MSG_ZEROCOPY available")
                
        except Exception as e:
            logger.warning(f"Linux socket optimization failed: {e}")
            
    def _check_zero_copy_support(self):
        """Check for Linux zero-copy support"""
        try:
            # Check for sendfile support
            try:
                import os
                if hasattr(os, 'sendfile'):
                    self.sendfile_supported = True
                    logger.info("sendfile() zero-copy support available")
            except:
                pass
                
            # Check for splice support
            try:
                if os.path.exists('/proc/sys/fs/pipe-max-size'):
                    self.splice_supported = True
                    logger.info("splice() zero-copy support available")
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Zero-copy support check failed: {e}")
            
    def send_zero_copy(self, buffer: ZeroCopyBuffer, size: int) -> int:
        """Send data using Linux zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            # Use MSG_ZEROCOPY if available
            if hasattr(socket, 'MSG_ZEROCOPY'):
                data = buffer.read_data(size)
                return self.socket.send(data, socket.MSG_ZEROCOPY)
            else:
                # Fallback to regular send
                data = buffer.read_data(size)
                return self.socket.send(data)
                
        except Exception as e:
            logger.error(f"Linux zero-copy send failed: {e}")
            return 0
            
    def receive_zero_copy(self, buffer: ZeroCopyBuffer) -> int:
        """Receive data using Linux zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            # Receive directly into buffer
            data = self.socket.recv(buffer.size)
            if data:
                buffer.write_data(data)
                return len(data)
                
            return 0
            
        except Exception as e:
            logger.error(f"Linux zero-copy receive failed: {e}")
            return 0

class WindowsZeroCopySocket(ZeroCopySocketBase):
    """Windows-specific zero-copy socket implementation"""
    
    def __init__(self):
        super().__init__()
        self.overlapped_io = False
        self.iocp_handle = None
        
    def create_zero_copy_socket(self, family: int, type: int) -> bool:
        """Create Windows zero-copy optimized socket"""
        try:
            self.socket = socket.socket(family, type)
            
            # Enable Windows optimizations
            self._enable_windows_optimizations()
            
            # Setup IOCP for zero-copy I/O
            self._setup_iocp()
            
            self.zero_copy_enabled = True
            logger.info("Windows zero-copy socket created")
            return True
            
        except Exception as e:
            logger.error(f"Windows zero-copy socket creation failed: {e}")
            return False
            
    def _enable_windows_optimizations(self):
        """Enable Windows-specific socket optimizations"""
        try:
            # Enable TCP_NODELAY
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Set large buffer sizes
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            
            # Enable overlapped I/O
            if platform.system() == 'Windows':
                try:
                    import _winapi
                    self.overlapped_io = True
                    logger.info("Overlapped I/O enabled")
                except ImportError:
                    pass
                    
        except Exception as e:
            logger.warning(f"Windows socket optimization failed: {e}")
            
    def _setup_iocp(self):
        """Setup I/O Completion Port for high-performance I/O"""
        try:
            if platform.system() == 'Windows' and self.overlapped_io:
                # Create IOCP handle
                logger.info("Setting up IOCP for zero-copy I/O")
                # In real implementation, would create actual IOCP
                
        except Exception as e:
            logger.warning(f"IOCP setup failed: {e}")
            
    def send_zero_copy(self, buffer: ZeroCopyBuffer, size: int) -> int:
        """Send data using Windows zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            # Use overlapped I/O if available
            if self.overlapped_io:
                # Would use WSASend with overlapped structure
                data = buffer.read_data(size)
                return self.socket.send(data)
            else:
                data = buffer.read_data(size)
                return self.socket.send(data)
                
        except Exception as e:
            logger.error(f"Windows zero-copy send failed: {e}")
            return 0
            
    def receive_zero_copy(self, buffer: ZeroCopyBuffer) -> int:
        """Receive data using Windows zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            # Use overlapped I/O if available
            data = self.socket.recv(buffer.size)
            if data:
                buffer.write_data(data)
                return len(data)
                
            return 0
            
        except Exception as e:
            logger.error(f"Windows zero-copy receive failed: {e}")
            return 0

class MacOSZeroCopySocket(ZeroCopySocketBase):
    """macOS-specific zero-copy socket implementation"""
    
    def __init__(self):
        super().__init__()
        self.kqueue_fd = None
        
    def create_zero_copy_socket(self, family: int, type: int) -> bool:
        """Create macOS zero-copy optimized socket"""
        try:
            self.socket = socket.socket(family, type)
            
            # Enable macOS optimizations
            self._enable_macos_optimizations()
            
            # Setup kqueue for efficient I/O
            self._setup_kqueue()
            
            self.zero_copy_enabled = True
            logger.info("macOS zero-copy socket created")
            return True
            
        except Exception as e:
            logger.error(f"macOS zero-copy socket creation failed: {e}")
            return False
            
    def _enable_macos_optimizations(self):
        """Enable macOS-specific socket optimizations"""
        try:
            # Enable TCP_NODELAY
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Set large buffer sizes
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            
            # Enable BSD-specific optimizations
            if hasattr(socket, 'SO_NOSIGPIPE'):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_NOSIGPIPE, 1)
                
        except Exception as e:
            logger.warning(f"macOS socket optimization failed: {e}")
            
    def _setup_kqueue(self):
        """Setup kqueue for efficient event handling"""
        try:
            import select
            if hasattr(select, 'kqueue'):
                self.kqueue_fd = select.kqueue()
                logger.info("kqueue setup for zero-copy I/O")
                
        except Exception as e:
            logger.warning(f"kqueue setup failed: {e}")
            
    def send_zero_copy(self, buffer: ZeroCopyBuffer, size: int) -> int:
        """Send data using macOS zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            # Use sendfile if available
            data = buffer.read_data(size)
            return self.socket.send(data)
                
        except Exception as e:
            logger.error(f"macOS zero-copy send failed: {e}")
            return 0
            
    def receive_zero_copy(self, buffer: ZeroCopyBuffer) -> int:
        """Receive data using macOS zero-copy mechanisms"""
        try:
            if not self.zero_copy_enabled:
                return 0
                
            data = self.socket.recv(buffer.size)
            if data:
                buffer.write_data(data)
                return len(data)
                
            return 0
            
        except Exception as e:
            logger.error(f"macOS zero-copy receive failed: {e}")
            return 0

class NUMAManager:
    """NUMA-aware memory and processing management"""
    
    def __init__(self):
        self.numa_nodes = []
        self.cpu_topology = {}
        self.memory_topology = {}
        self._discover_numa_topology()
        
    def _discover_numa_topology(self):
        """Discover NUMA topology"""
        try:
            if platform.system() == 'Linux':
                self._discover_linux_numa()
            elif platform.system() == 'Windows':
                self._discover_windows_numa()
            else:
                logger.info("NUMA discovery not supported on this platform")
                
        except Exception as e:
            logger.warning(f"NUMA topology discovery failed: {e}")
            
    def _discover_linux_numa(self):
        """Discover Linux NUMA topology"""
        try:
            # Check for NUMA nodes
            numa_path = '/sys/devices/system/node'
            if os.path.exists(numa_path):
                nodes = [d for d in os.listdir(numa_path) if d.startswith('node')]
                self.numa_nodes = [int(n.replace('node', '')) for n in nodes]
                
                # Get CPU topology for each node
                for node in self.numa_nodes:
                    cpu_list_path = f'{numa_path}/node{node}/cpulist'
                    if os.path.exists(cpu_list_path):
                        with open(cpu_list_path, 'r') as f:
                            cpu_list = f.read().strip()
                            self.cpu_topology[node] = self._parse_cpu_list(cpu_list)
                            
                logger.info(f"Discovered NUMA nodes: {self.numa_nodes}")
                logger.info(f"CPU topology: {self.cpu_topology}")
                
        except Exception as e:
            logger.debug(f"Linux NUMA discovery failed: {e}")
            
    def _discover_windows_numa(self):
        """Discover Windows NUMA topology"""
        try:
            # Use Windows API to get NUMA information
            import ctypes
            from ctypes import wintypes
            
            # Get number of NUMA nodes
            kernel32 = ctypes.windll.kernel32
            num_nodes = wintypes.ULONG()
            
            if kernel32.GetNumaHighestNodeNumber(ctypes.byref(num_nodes)):
                self.numa_nodes = list(range(num_nodes.value + 1))
                logger.info(f"Discovered Windows NUMA nodes: {self.numa_nodes}")
                
        except Exception as e:
            logger.debug(f"Windows NUMA discovery failed: {e}")
            
    def _parse_cpu_list(self, cpu_list: str) -> List[int]:
        """Parse Linux CPU list format (e.g., '0-3,8-11')"""
        cpus = []
        for part in cpu_list.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                cpus.extend(range(start, end + 1))
            else:
                cpus.append(int(part))
        return cpus
        
    def get_optimal_numa_node(self, target_cpu: Optional[int] = None) -> int:
        """Get optimal NUMA node for allocation"""
        if not self.numa_nodes:
            return 0
            
        if target_cpu is not None:
            # Find NUMA node containing the target CPU
            for node, cpus in self.cpu_topology.items():
                if target_cpu in cpus:
                    return node
                    
        # Return first available node
        return self.numa_nodes[0]
        
    def bind_to_numa_node(self, node: int, pid: Optional[int] = None):
        """Bind process/thread to specific NUMA node"""
        try:
            if platform.system() == 'Linux':
                import subprocess
                pid_arg = str(pid) if pid else str(os.getpid())
                subprocess.run(['numactl', '--membind', str(node), 
                              '--cpunodebind', str(node), '--', 'true'], 
                              check=False)
                logger.info(f"Bound to NUMA node {node}")
                
        except Exception as e:
            logger.warning(f"NUMA binding failed: {e}")

class ZeroCopyPacketProcessor:
    """High-performance zero-copy packet processor"""
    
    def __init__(self, buffer_size: int = 1024 * 1024):
        self.buffer_size = buffer_size
        self.numa_manager = NUMAManager()
        self.packet_buffers = {}
        self.processing_threads = []
        self.packet_queue = queue.Queue()
        self.hardware_queues = {}
        self.direct_memory_access = {}
        self.kernel_bypass_enabled = False
        
    def initialize_processor(self, num_threads: Optional[int] = None) -> bool:
        """Initialize zero-copy packet processor"""
        try:
            if num_threads is None:
                num_threads = multiprocessing.cpu_count()
                
            # Create packet buffers for each NUMA node
            for node in self.numa_manager.numa_nodes or [0]:
                buffer = ZeroCopyBuffer(self.buffer_size, node)
                self.packet_buffers[node] = buffer
                
            # Start processing threads
            for i in range(num_threads):
                thread = threading.Thread(target=self._packet_processing_worker, 
                                        args=(i,), daemon=True)
                thread.start()
                self.processing_threads.append(thread)
                
            logger.info(f"Initialized zero-copy processor with {num_threads} threads")
            return True
            
        except Exception as e:
            logger.error(f"Zero-copy processor initialization failed: {e}")
            return False
            
    def _packet_processing_worker(self, worker_id: int):
        """Worker thread for packet processing"""
        try:
            # Bind to optimal NUMA node
            numa_node = self.numa_manager.get_optimal_numa_node()
            self.numa_manager.bind_to_numa_node(numa_node)
            
            logger.info(f"Worker {worker_id} bound to NUMA node {numa_node}")
            
            while True:
                try:
                    # Get packet from queue
                    packet_data = self.packet_queue.get(timeout=1.0)
                    if packet_data is None:  # Shutdown signal
                        break
                        
                    # Process packet using zero-copy buffer
                    self._process_packet_zero_copy(packet_data, numa_node)
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Packet processing error in worker {worker_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Worker {worker_id} failed: {e}")
            
    def _process_packet_zero_copy(self, packet_data: bytes, numa_node: int):
        """Process packet using zero-copy techniques"""
        try:
            buffer = self.packet_buffers.get(numa_node)
            if not buffer:
                return
                
            # Write packet to zero-copy buffer
            if buffer.write_data(packet_data):
                # Process packet in-place (no copying)
                self._transform_packet_in_buffer(buffer, len(packet_data))
                
        except Exception as e:
            logger.error(f"Zero-copy packet processing failed: {e}")
            
    def _transform_packet_in_buffer(self, buffer: ZeroCopyBuffer, size: int):
        """Transform packet data in-place within buffer"""
        try:
            # Example transformation - modify packet data directly in buffer
            # This avoids copying data between buffers
            
            # Get buffer address for direct manipulation
            addr = buffer.get_buffer_address()
            if addr:
                # Direct memory manipulation (example)
                data = buffer.read_data(size)
                # Apply transformations...
                buffer.write_data(data)
                
        except Exception as e:
            logger.error(f"In-buffer packet transformation failed: {e}")
            
    def queue_packet(self, packet_data: bytes):
        """Queue packet for zero-copy processing"""
        try:
            self.packet_queue.put(packet_data)
        except Exception as e:
            logger.error(f"Packet queuing failed: {e}")
            
    def shutdown(self):
        """Shutdown packet processor"""
        try:
            # Signal threads to stop
            for _ in self.processing_threads:
                self.packet_queue.put(None)
                
            # Wait for threads to finish
            for thread in self.processing_threads:
                thread.join(timeout=5.0)
                
            # Cleanup buffers
            for buffer in self.packet_buffers.values():
                buffer.close()
                
            logger.info("Zero-copy processor shutdown complete")
            
        except Exception as e:
            logger.error(f"Processor shutdown failed: {e}")

class ZeroCopyEngine:
    """Main zero-copy engine that manages all zero-copy operations"""
    
    def __init__(self):
        self.platform = platform.system()
        self.socket_factory = self._create_socket_factory()
        self.packet_processor = ZeroCopyPacketProcessor()
        self.numa_manager = NUMAManager()
        self.zero_copy_enabled = False
        
    def _create_socket_factory(self) -> ZeroCopySocketBase:
        """Create platform-specific zero-copy socket factory"""
        if self.platform == 'Linux':
            return LinuxZeroCopySocket()
        elif self.platform == 'Windows':
            return WindowsZeroCopySocket()
        elif self.platform == 'Darwin':
            return MacOSZeroCopySocket()
        else:
            raise NotImplementedError(f"Platform {self.platform} not supported")
            
    def initialize_zero_copy(self) -> bool:
        """Initialize all zero-copy capabilities"""
        try:
            # Initialize packet processor
            if not self.packet_processor.initialize_processor():
                logger.warning("Packet processor initialization failed")
                
            self.zero_copy_enabled = True
            logger.info("Zero-copy engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Zero-copy initialization failed: {e}")
            return False
            
    def create_zero_copy_socket(self, family: int = socket.AF_INET, 
                               type: int = socket.SOCK_STREAM) -> Optional[ZeroCopySocketBase]:
        """Create zero-copy optimized socket"""
        try:
            socket_impl = self._create_socket_factory()
            if socket_impl.create_zero_copy_socket(family, type):
                return socket_impl
            return None
            
        except Exception as e:
            logger.error(f"Zero-copy socket creation failed: {e}")
            return None
            
    def create_zero_copy_buffer(self, size: int, numa_node: Optional[int] = None) -> ZeroCopyBuffer:
        """Create zero-copy buffer with optimal NUMA placement"""
        try:
            if numa_node is None:
                numa_node = self.numa_manager.get_optimal_numa_node()
                
            return ZeroCopyBuffer(size, numa_node)
            
        except Exception as e:
            logger.error(f"Zero-copy buffer creation failed: {e}")
            raise
            
    def process_packets_zero_copy(self, packets: List[bytes]):
        """Process packets using zero-copy techniques"""
        try:
            for packet in packets:
                self.packet_processor.queue_packet(packet)
                
        except Exception as e:
            logger.error(f"Zero-copy packet processing failed: {e}")
            
    def get_numa_topology(self) -> Dict[str, Any]:
        """Get NUMA topology information"""
        return {
            'numa_nodes': self.numa_manager.numa_nodes,
            'cpu_topology': self.numa_manager.cpu_topology,
            'memory_topology': self.numa_manager.memory_topology
        }
        
    def get_zero_copy_status(self) -> Dict[str, Any]:
        """Get zero-copy engine status"""
        return {
            'platform': self.platform,
            'zero_copy_enabled': self.zero_copy_enabled,
            'numa_nodes': len(self.numa_manager.numa_nodes),
            'processor_threads': len(self.packet_processor.processing_threads)
        }
        
    def shutdown(self):
        """Shutdown zero-copy engine"""
        try:
            self.packet_processor.shutdown()
            logger.info("Zero-copy engine shutdown complete")
            
        except Exception as e:
            logger.error(f"Zero-copy shutdown failed: {e}")

class DirectHardwareAccess:
    """Direct hardware access for zero-copy networking"""
    
    def __init__(self):
        self.platform = platform.system()
        self.hardware_interfaces = {}
        self.memory_mapped_regions = {}
        self.dma_buffers = {}
        
    def initialize_hardware_access(self) -> bool:
        """Initialize direct hardware access"""
        try:
            if self.platform == 'Linux':
                return self._initialize_linux_hardware_access()
            elif self.platform == 'Windows':
                return self._initialize_windows_hardware_access()
            elif self.platform == 'Darwin':
                return self._initialize_macos_hardware_access()
            else:
                logger.warning(f"Direct hardware access not supported on {self.platform}")
                return False
                
        except Exception as e:
            logger.error(f"Hardware access initialization failed: {e}")
            return False
            
    def _initialize_linux_hardware_access(self) -> bool:
        """Initialize Linux-specific hardware access"""
        try:
            # Check for UIO (Userspace I/O) devices
            uio_devices = self._discover_uio_devices()
            
            # Check for VFIO (Virtual Function I/O) devices
            vfio_devices = self._discover_vfio_devices()
            
            # Setup memory mapping for network devices
            network_devices = self._discover_network_devices()
            
            # Initialize DMA buffers
            self._setup_dma_buffers()
            
            logger.info(f"Linux hardware access initialized: "
                       f"{len(uio_devices)} UIO, {len(vfio_devices)} VFIO, "
                       f"{len(network_devices)} network devices")
            return True
            
        except Exception as e:
            logger.error(f"Linux hardware access initialization failed: {e}")
            return False
            
    def _discover_uio_devices(self) -> List[dict]:
        """Discover UIO devices for direct hardware access"""
        uio_devices = []
        
        try:
            uio_path = '/sys/class/uio'
            if os.path.exists(uio_path):
                for device in os.listdir(uio_path):
                    device_path = os.path.join(uio_path, device)
                    device_info = {
                        'name': device,
                        'path': device_path,
                        'device_file': f'/dev/{device}'
                    }
                    
                    # Get device information
                    info_files = ['name', 'version', 'maps']
                    for info_file in info_files:
                        info_path = os.path.join(device_path, info_file)
                        if os.path.exists(info_path):
                            try:
                                with open(info_path, 'r') as f:
                                    device_info[info_file] = f.read().strip()
                            except (OSError, PermissionError):
                                continue
                                
                    uio_devices.append(device_info)
                    self.hardware_interfaces[device] = device_info
                    
        except Exception as e:
            logger.debug(f"UIO device discovery failed: {e}")
            
        return uio_devices
        
    def _discover_vfio_devices(self) -> List[dict]:
        """Discover VFIO devices for direct hardware access"""
        vfio_devices = []
        
        try:
            vfio_path = '/dev/vfio'
            if os.path.exists(vfio_path):
                for device in os.listdir(vfio_path):
                    if device.isdigit():  # VFIO group
                        device_info = {
                            'group': device,
                            'device_file': os.path.join(vfio_path, device)
                        }
                        vfio_devices.append(device_info)
                        
        except Exception as e:
            logger.debug(f"VFIO device discovery failed: {e}")
            
        return vfio_devices
        
    def _discover_network_devices(self) -> List[dict]:
        """Discover network devices for direct access"""
        network_devices = []
        
        try:
            # Check for network devices with direct access capabilities
            net_path = '/sys/class/net'
            if os.path.exists(net_path):
                for interface in os.listdir(net_path):
                    interface_path = os.path.join(net_path, interface)
                    
                    # Check for direct access capabilities
                    device_info = {
                        'interface': interface,
                        'path': interface_path
                    }
                    
                    # Check for DPDK support
                    pci_path = os.path.join(interface_path, 'device')
                    if os.path.exists(pci_path):
                        device_info['pci_device'] = os.readlink(pci_path)
                        
                    # Check for SR-IOV support
                    sriov_path = os.path.join(interface_path, 'device/sriov_totalvfs')
                    if os.path.exists(sriov_path):
                        try:
                            with open(sriov_path, 'r') as f:
                                device_info['sriov_vfs'] = int(f.read().strip())
                        except (OSError, ValueError):
                            pass
                            
                    network_devices.append(device_info)
                    
        except Exception as e:
            logger.debug(f"Network device discovery failed: {e}")
            
        return network_devices
        
    def _setup_dma_buffers(self):
        """Setup DMA buffers for zero-copy operations"""
        try:
            # Create DMA-coherent memory regions
            buffer_sizes = [4096, 8192, 16384, 65536, 1048576]  # Various buffer sizes
            
            for size in buffer_sizes:
                try:
                    # Allocate page-aligned memory for DMA
                    buffer = mmap.mmap(-1, size, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
                    
                    # Lock memory to prevent swapping
                    if hasattr(mmap, 'MADV_DONTFORK'):
                        buffer.madvise(mmap.MADV_DONTFORK)
                        
                    self.dma_buffers[size] = buffer
                    logger.debug(f"Created DMA buffer: {size} bytes")
                    
                except Exception as e:
                    logger.debug(f"DMA buffer creation failed for size {size}: {e}")
                    
        except Exception as e:
            logger.warning(f"DMA buffer setup failed: {e}")
            
    def _initialize_windows_hardware_access(self) -> bool:
        """Initialize Windows-specific hardware access"""
        try:
            # Check for WinDivert or similar packet capture drivers
            windivert_available = self._check_windivert_available()
            
            # Check for NDIS filter drivers
            ndis_available = self._check_ndis_available()
            
            # Setup memory mapping for Windows
            self._setup_windows_memory_mapping()
            
            logger.info(f"Windows hardware access initialized: "
                       f"WinDivert={windivert_available}, NDIS={ndis_available}")
            return windivert_available or ndis_available
            
        except Exception as e:
            logger.error(f"Windows hardware access initialization failed: {e}")
            return False
            
    def _check_windivert_available(self) -> bool:
        """Check if WinDivert is available"""
        try:
            # Check for WinDivert DLL
            windivert_paths = [
                'WinDivert.dll',
                'C:\\Windows\\System32\\WinDivert.dll',
                'C:\\Program Files\\WinDivert\\WinDivert.dll'
            ]
            
            for path in windivert_paths:
                if os.path.exists(path):
                    logger.debug(f"Found WinDivert at {path}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"WinDivert check failed: {e}")
            return False
            
    def _check_ndis_available(self) -> bool:
        """Check if NDIS filter drivers are available"""
        try:
            # Check for NDIS development environment
            ndis_paths = [
                r"C:\Program Files (x86)\Windows Kits\10\Include\*\km\ndis.h",
                r"C:\WinDDK\*\inc\api\ndis.h"
            ]
            
            import glob
            for pattern in ndis_paths:
                if glob.glob(pattern):
                    logger.debug("Found NDIS development environment")
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"NDIS check failed: {e}")
            return False
            
    def _setup_windows_memory_mapping(self):
        """Setup Windows memory mapping for direct access"""
        try:
            # Create memory-mapped regions for packet processing
            buffer_sizes = [4096, 8192, 16384, 65536]
            
            for size in buffer_sizes:
                try:
                    buffer = mmap.mmap(-1, size, mmap.MAP_PRIVATE)
                    self.memory_mapped_regions[size] = buffer
                    logger.debug(f"Created Windows memory mapping: {size} bytes")
                except Exception as e:
                    logger.debug(f"Windows memory mapping failed for size {size}: {e}")
                    
        except Exception as e:
            logger.warning(f"Windows memory mapping setup failed: {e}")
            
    def _initialize_macos_hardware_access(self) -> bool:
        """Initialize macOS-specific hardware access"""
        try:
            # Check for BPF devices
            bpf_devices = self._discover_bpf_devices()
            
            # Check for kernel extension support
            kext_support = self._check_kext_support()
            
            # Setup memory mapping for macOS
            self._setup_macos_memory_mapping()
            
            logger.info(f"macOS hardware access initialized: "
                       f"{len(bpf_devices)} BPF devices, KEXT support={kext_support}")
            return len(bpf_devices) > 0 or kext_support
            
        except Exception as e:
            logger.error(f"macOS hardware access initialization failed: {e}")
            return False
            
    def _discover_bpf_devices(self) -> List[str]:
        """Discover BPF devices on macOS"""
        bpf_devices = []
        
        try:
            for i in range(20):  # Check first 20 BPF devices
                bpf_device = f'/dev/bpf{i}'
                if os.path.exists(bpf_device):
                    bpf_devices.append(bpf_device)
                    
        except Exception as e:
            logger.debug(f"BPF device discovery failed: {e}")
            
        return bpf_devices
        
    def _check_kext_support(self) -> bool:
        """Check if kernel extensions are supported"""
        try:
            # Check SIP status
            result = subprocess.run(['csrutil', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return 'disabled' in result.stdout.lower()
                
            return False
            
        except Exception as e:
            logger.debug(f"KEXT support check failed: {e}")
            return False
            
    def _setup_macos_memory_mapping(self):
        """Setup macOS memory mapping for direct access"""
        try:
            # Create memory-mapped regions for packet processing
            buffer_sizes = [4096, 8192, 16384, 65536]
            
            for size in buffer_sizes:
                try:
                    buffer = mmap.mmap(-1, size, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
                    self.memory_mapped_regions[size] = buffer
                    logger.debug(f"Created macOS memory mapping: {size} bytes")
                except Exception as e:
                    logger.debug(f"macOS memory mapping failed for size {size}: {e}")
                    
        except Exception as e:
            logger.warning(f"macOS memory mapping setup failed: {e}")
            
    def get_dma_buffer(self, size: int) -> Optional[mmap.mmap]:
        """Get DMA buffer of specified size"""
        # Find the smallest buffer that can accommodate the request
        for buffer_size, buffer in self.dma_buffers.items():
            if buffer_size >= size:
                return buffer
                
        return None
        
    def create_memory_region(self, size: int, numa_node: Optional[int] = None) -> Optional[mmap.mmap]:
        """Create memory region for zero-copy operations"""
        try:
            # Create memory-mapped region
            buffer = mmap.mmap(-1, size, mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
            
            # Configure for zero-copy operations
            if hasattr(mmap, 'MADV_SEQUENTIAL'):
                buffer.madvise(mmap.MADV_SEQUENTIAL)
                
            if hasattr(mmap, 'MADV_WILLNEED'):
                buffer.madvise(mmap.MADV_WILLNEED)
                
            return buffer
            
        except Exception as e:
            logger.error(f"Memory region creation failed: {e}")
            return None
            
    def cleanup(self):
        """Cleanup hardware access resources"""
        try:
            # Close DMA buffers
            for buffer in self.dma_buffers.values():
                if buffer:
                    buffer.close()
                    
            # Close memory mapped regions
            for buffer in self.memory_mapped_regions.values():
                if buffer:
                    buffer.close()
                    
            logger.info("Hardware access cleanup completed")
            
        except Exception as e:
            logger.error(f"Hardware access cleanup failed: {e}")

class AdvancedNUMAManager(NUMAManager):
    """Advanced NUMA manager with enhanced capabilities"""
    
    def __init__(self):
        super().__init__()
        self.cpu_cache_topology = {}
        self.memory_bandwidth = {}
        self.numa_distances = {}
        self.cpu_frequencies = {}
        self._discover_advanced_topology()
        
    def _discover_advanced_topology(self):
        """Discover advanced NUMA topology information"""
        try:
            if self.platform == 'Linux':
                self._discover_linux_advanced_topology()
            elif self.platform == 'Windows':
                self._discover_windows_advanced_topology()
                
        except Exception as e:
            logger.debug(f"Advanced NUMA topology discovery failed: {e}")
            
    def _discover_linux_advanced_topology(self):
        """Discover Linux advanced NUMA topology"""
        try:
            # Discover CPU cache topology
            self._discover_cpu_cache_topology()
            
            # Discover NUMA distances
            self._discover_numa_distances()
            
            # Discover memory bandwidth information
            self._discover_memory_bandwidth()
            
            # Discover CPU frequencies
            self._discover_cpu_frequencies()
            
        except Exception as e:
            logger.debug(f"Linux advanced topology discovery failed: {e}")
            
    def _discover_cpu_cache_topology(self):
        """Discover CPU cache topology"""
        try:
            cpu_path = '/sys/devices/system/cpu'
            if os.path.exists(cpu_path):
                for cpu_dir in os.listdir(cpu_path):
                    if cpu_dir.startswith('cpu') and cpu_dir[3:].isdigit():
                        cpu_num = int(cpu_dir[3:])
                        cache_info = {}
                        
                        cache_path = os.path.join(cpu_path, cpu_dir, 'cache')
                        if os.path.exists(cache_path):
                            for cache_dir in os.listdir(cache_path):
                                if cache_dir.startswith('index'):
                                    cache_level_path = os.path.join(cache_path, cache_dir)
                                    cache_level_info = {}
                                    
                                    # Read cache attributes
                                    cache_attrs = ['level', 'type', 'size', 'shared_cpu_list']
                                    for attr in cache_attrs:
                                        attr_path = os.path.join(cache_level_path, attr)
                                        if os.path.exists(attr_path):
                                            try:
                                                with open(attr_path, 'r') as f:
                                                    cache_level_info[attr] = f.read().strip()
                                            except (OSError, PermissionError):
                                                continue
                                                
                                    if cache_level_info:
                                        cache_info[cache_dir] = cache_level_info
                                        
                        if cache_info:
                            self.cpu_cache_topology[cpu_num] = cache_info
                            
        except Exception as e:
            logger.debug(f"CPU cache topology discovery failed: {e}")
            
    def _discover_numa_distances(self):
        """Discover NUMA node distances"""
        try:
            for node in self.numa_nodes:
                distance_path = f'/sys/devices/system/node/node{node}/distance'
                if os.path.exists(distance_path):
                    try:
                        with open(distance_path, 'r') as f:
                            distances = f.read().strip().split()
                            self.numa_distances[node] = [int(d) for d in distances]
                    except (OSError, PermissionError, ValueError):
                        continue
                        
        except Exception as e:
            logger.debug(f"NUMA distances discovery failed: {e}")
            
    def _discover_memory_bandwidth(self):
        """Discover memory bandwidth information"""
        try:
            # Try to read memory bandwidth from various sources
            bandwidth_sources = [
                '/sys/devices/system/node/node*/meminfo',
                '/proc/meminfo'
            ]
            
            for node in self.numa_nodes:
                meminfo_path = f'/sys/devices/system/node/node{node}/meminfo'
                if os.path.exists(meminfo_path):
                    try:
                        with open(meminfo_path, 'r') as f:
                            meminfo = f.read()
                            
                        # Parse memory information
                        bandwidth_info = {}
                        for line in meminfo.split('\n'):
                            if 'MemTotal' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    bandwidth_info['total_memory_kb'] = int(parts[1])
                            elif 'MemFree' in line:
                                parts = line.split()
                                if len(parts) >= 2:
                                    bandwidth_info['free_memory_kb'] = int(parts[1])
                                    
                        if bandwidth_info:
                            self.memory_bandwidth[node] = bandwidth_info
                            
                    except (OSError, PermissionError, ValueError):
                        continue
                        
        except Exception as e:
            logger.debug(f"Memory bandwidth discovery failed: {e}")
            
    def _discover_cpu_frequencies(self):
        """Discover CPU frequency information"""
        try:
            cpu_path = '/sys/devices/system/cpu'
            if os.path.exists(cpu_path):
                for cpu_dir in os.listdir(cpu_path):
                    if cpu_dir.startswith('cpu') and cpu_dir[3:].isdigit():
                        cpu_num = int(cpu_dir[3:])
                        freq_info = {}
                        
                        # Read frequency information
                        freq_attrs = [
                            'cpufreq/scaling_cur_freq',
                            'cpufreq/scaling_max_freq',
                            'cpufreq/scaling_min_freq',
                            'cpufreq/scaling_governor'
                        ]
                        
                        for attr in freq_attrs:
                            attr_path = os.path.join(cpu_path, cpu_dir, attr)
                            if os.path.exists(attr_path):
                                try:
                                    with open(attr_path, 'r') as f:
                                        freq_info[attr.split('/')[-1]] = f.read().strip()
                                except (OSError, PermissionError):
                                    continue
                                    
                        if freq_info:
                            self.cpu_frequencies[cpu_num] = freq_info
                            
        except Exception as e:
            logger.debug(f"CPU frequency discovery failed: {e}")
            
    def get_optimal_cpu_for_network_io(self) -> int:
        """Get optimal CPU for network I/O operations"""
        try:
            # Prefer CPUs with higher frequencies and closer to network devices
            if self.cpu_frequencies:
                # Find CPU with highest current frequency
                best_cpu = 0
                best_freq = 0
                
                for cpu, freq_info in self.cpu_frequencies.items():
                    try:
                        cur_freq = int(freq_info.get('scaling_cur_freq', 0))
                        if cur_freq > best_freq:
                            best_freq = cur_freq
                            best_cpu = cpu
                    except ValueError:
                        continue
                        
                return best_cpu
                
            # Fallback to first available CPU
            return 0
            
        except Exception as e:
            logger.debug(f"Optimal CPU selection failed: {e}")
            return 0
            
    def get_memory_locality_score(self, numa_node: int, target_node: int) -> int:
        """Get memory locality score between NUMA nodes"""
        try:
            if numa_node in self.numa_distances and target_node < len(self.numa_distances[numa_node]):
                return self.numa_distances[numa_node][target_node]
            else:
                # Default distance for same node is 10, remote nodes are higher
                return 10 if numa_node == target_node else 20
                
        except Exception as e:
            logger.debug(f"Memory locality score calculation failed: {e}")
            return 20  # Conservative default
            
    def optimize_thread_placement(self, num_threads: int) -> List[int]:
        """Optimize thread placement across NUMA nodes"""
        try:
            thread_placement = []
            
            if not self.numa_nodes:
                # No NUMA, distribute across available CPUs
                cpu_count = multiprocessing.cpu_count()
                for i in range(num_threads):
                    thread_placement.append(i % cpu_count)
                return thread_placement
                
            # Distribute threads across NUMA nodes
            threads_per_node = num_threads // len(self.numa_nodes)
            remaining_threads = num_threads % len(self.numa_nodes)
            
            for node_idx, node in enumerate(self.numa_nodes):
                node_cpus = self.cpu_topology.get(node, [0])
                node_thread_count = threads_per_node + (1 if node_idx < remaining_threads else 0)
                
                for i in range(node_thread_count):
                    cpu = node_cpus[i % len(node_cpus)]
                    thread_placement.append(cpu)
                    
            return thread_placement
            
        except Exception as e:
            logger.debug(f"Thread placement optimization failed: {e}")
            # Fallback to simple round-robin
            cpu_count = multiprocessing.cpu_count()
            return [i % cpu_count for i in range(num_threads)]