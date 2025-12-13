# NetStress Platform Capabilities

This document provides a comprehensive overview of NetStress features and limitations across different platforms.

## Architecture Overview

NetStress uses a "Power Trio" sandwich architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON LAYER (Brain)                                 │
│  ddos.py │ main.py │ CLI │ AI/ML │ Analytics │ Configuration │ Reporting   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         RUST LAYER (Engine)                                  │
│  netstress_engine (PyO3) │ Packet Gen │ Threading │ Lock-Free Queues        │
├─────────────────────────────────────────────────────────────────────────────┤
│                         C LAYER (Metal)                                      │
│  driver_shim.c │ DPDK │ AF_XDP │ io_uring │ sendmmsg │ Raw Sockets          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Platform Support Matrix

### Linux (Primary Platform)

| Feature         | Availability    | Requirements              | Performance   |
| --------------- | --------------- | ------------------------- | ------------- |
| **Python Mode** | ✅ Always       | Python 3.8+               | 500K-2M PPS   |
| **Rust Engine** | ✅ Optional     | Rust 1.70+, maturin       | 1M-10M PPS    |
| **Raw Sockets** | ✅ Always       | Root privileges           | 50K-500K PPS  |
| **sendmmsg**    | ✅ Kernel 3.0+  | Root privileges           | 500K-2M PPS   |
| **io_uring**    | ✅ Kernel 5.1+  | Root privileges           | 1M-10M PPS    |
| **AF_XDP**      | ⚠️ Kernel 4.18+ | Root, libbpf-dev          | 10M-50M PPS   |
| **DPDK**        | ⚠️ Optional     | DPDK libraries, hugepages | 50M-100M+ PPS |

**Linux Optimizations:**

- Zero-copy operations with `MSG_ZEROCOPY`
- Batch sending with `sendmmsg()`
- Async I/O with `io_uring`
- Kernel bypass with DPDK/AF_XDP
- NUMA-aware memory allocation
- CPU affinity and IRQ balancing

### Windows

| Feature            | Availability      | Requirements             | Performance   |
| ------------------ | ----------------- | ------------------------ | ------------- |
| **Python Mode**    | ✅ Always         | Python 3.8+              | 50K-200K PPS  |
| **Rust Engine**    | ✅ Optional       | Rust 1.70+, maturin      | 200K-1M PPS   |
| **Raw Sockets**    | ✅ Always         | Administrator privileges | 10K-100K PPS  |
| **IOCP**           | ✅ Windows Vista+ | Administrator privileges | 100K-500K PPS |
| **Registered I/O** | ⚠️ Windows 8+     | Administrator privileges | 200K-1M PPS   |
| **Winsock2**       | ✅ Always         | Standard sockets         | 50K-200K PPS  |

**Windows Limitations:**

- No kernel bypass networking (no DPDK/AF_XDP equivalent)
- Limited raw socket support compared to Linux
- Windows Defender may flag the tool
- Performance limited by Windows network stack

### macOS

| Feature         | Availability | Requirements        | Performance   |
| --------------- | ------------ | ------------------- | ------------- |
| **Python Mode** | ✅ Always    | Python 3.8+         | 100K-500K PPS |
| **Rust Engine** | ✅ Optional  | Rust 1.70+, maturin | 200K-1M PPS   |
| **Raw Sockets** | ✅ Always    | Root privileges     | 50K-200K PPS  |
| **kqueue**      | ✅ Always    | Root privileges     | 100K-500K PPS |
| **BSD Sockets** | ✅ Always    | Standard sockets    | 100K-300K PPS |

**macOS Limitations:**

- No kernel bypass networking
- Limited to BSD socket optimizations
- SIP (System Integrity Protection) may interfere
- Performance limited by macOS network stack

## Backend Selection Priority

The engine automatically selects the best available backend in this order:

### Linux Priority

1. **DPDK** - Kernel bypass, maximum performance
2. **AF_XDP** - Zero-copy kernel bypass
3. **io_uring** - Async I/O with batching
4. **sendmmsg** - Batch syscalls
5. **Raw Socket** - Standard fallback

### Windows Priority

1. **Registered I/O** - High-performance async I/O
2. **IOCP** - I/O Completion Ports
3. **Raw Socket** - Standard fallback

### macOS Priority

1. **kqueue** - Event-driven I/O
2. **Raw Socket** - Standard fallback

## Performance Expectations

### Realistic Performance Ranges

| Platform    | Mode          | UDP PPS   | TCP Conn/sec | Bandwidth   |
| ----------- | ------------- | --------- | ------------ | ----------- |
| **Linux**   | Python        | 500K-2M   | 10K-50K      | 1-10 Gbps   |
|             | Rust          | 1M-10M    | 50K-200K     | 5-40 Gbps   |
|             | Rust + AF_XDP | 10M-50M   | N/A          | 40-100 Gbps |
|             | Rust + DPDK   | 50M-100M+ | N/A          | 100+ Gbps   |
| **Windows** | Python        | 50K-200K  | 2K-10K       | 100M-2G     |
|             | Rust          | 200K-1M   | 10K-50K      | 1-5 Gbps    |
| **macOS**   | Python        | 100K-500K | 5K-20K       | 500M-5G     |
|             | Rust          | 200K-1M   | 10K-50K      | 1-5 Gbps    |

### Performance Factors

**Positive Factors:**

- Multiple CPU cores
- High-speed network interface (10G+)
- Sufficient RAM (8GB+)
- SSD storage
- Dedicated network hardware
- Proper kernel tuning

**Limiting Factors:**

- Python GIL (Global Interpreter Lock)
- OS network stack overhead
- Memory allocation/garbage collection
- Network interface limitations
- Target system capacity

## Feature Availability

### Core Features (All Platforms)

| Feature             | Linux | Windows | macOS | Notes                             |
| ------------------- | ----- | ------- | ----- | --------------------------------- |
| **UDP Flood**       | ✅    | ✅      | ✅    | Basic packet flooding             |
| **TCP Flood**       | ✅    | ✅      | ✅    | Connection-based attacks          |
| **HTTP Flood**      | ✅    | ✅      | ✅    | Layer 7 attacks                   |
| **Rate Limiting**   | ✅    | ✅      | ✅    | Precision rate control            |
| **Statistics**      | ✅    | ✅      | ✅    | Real-time metrics                 |
| **Safety Controls** | ✅    | ✅      | ✅    | Target validation, emergency stop |

### Advanced Features

| Feature                  | Linux | Windows | macOS | Notes                                  |
| ------------------------ | ----- | ------- | ----- | -------------------------------------- |
| **IP Spoofing**          | ✅    | ⚠️      | ⚠️    | Requires raw sockets, admin privileges |
| **Packet Fragmentation** | ✅    | ⚠️      | ⚠️    | Limited on Windows/macOS               |
| **SIMD Acceleration**    | ✅    | ✅      | ✅    | AVX2/SSE2 checksum calculation         |
| **Lock-Free Queues**     | ✅    | ✅      | ✅    | MPMC queues for threading              |
| **Zero-Copy I/O**        | ✅    | ⚠️      | ⚠️    | MSG_ZEROCOPY on Linux only             |
| **Batch Operations**     | ✅    | ⚠️      | ⚠️    | sendmmsg on Linux, limited elsewhere   |

### AI/ML Features (All Platforms)

| Feature                    | Availability | Requirements | Notes                       |
| -------------------------- | ------------ | ------------ | --------------------------- |
| **Genetic Algorithm**      | ✅           | Python 3.8+  | Parameter optimization      |
| **Reinforcement Learning** | ✅           | Python 3.8+  | Adaptive attack tuning      |
| **Defense Detection**      | ✅           | Python 3.8+  | WAF/rate limiting detection |
| **Traffic Analysis**       | ✅           | Python 3.8+  | Pattern recognition         |
| **Predictive Analytics**   | ✅           | Python 3.8+  | Performance prediction      |

### Evasion Features (All Platforms)

| Feature                       | Availability | Requirements | Notes                    |
| ----------------------------- | ------------ | ------------ | ------------------------ |
| **Traffic Shaping**           | ✅           | Python 3.8+  | Rate/timing manipulation |
| **Protocol Obfuscation**      | ✅           | Python 3.8+  | XOR encoding, mimicry    |
| **Proxy Chains**              | ✅           | Python 3.8+  | SOCKS/HTTP proxy support |
| **Fingerprint Randomization** | ✅           | Python 3.8+  | Browser/TLS fingerprints |
| **Behavioral Mimicry**        | ✅           | Python 3.8+  | Human-like patterns      |

## Build Requirements

### Linux

```bash
# Base requirements
sudo apt update
sudo apt install python3 python3-pip build-essential

# Rust engine (optional)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install maturin

# Advanced features (optional)
sudo apt install dpdk dpdk-dev          # DPDK support
sudo apt install libbpf-dev             # AF_XDP support
sudo apt install linux-headers-$(uname -r)  # Kernel headers
```

### Windows

```powershell
# Base requirements
# Install Python 3.8+ from python.org
# Install Visual Studio Build Tools

# Rust engine (optional)
# Install Rust from rustup.rs
pip install maturin

# Run as Administrator for raw socket support
```

### macOS

```bash
# Base requirements
brew install python3

# Rust engine (optional)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install maturin

# Xcode Command Line Tools
xcode-select --install
```

## Runtime Requirements

### Minimum System Requirements

- **CPU:** 2+ cores, x86_64 or ARM64
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 1GB free space
- **Network:** 100Mbps+ interface
- **OS:** Linux 3.0+, Windows 10+, macOS 10.14+

### Recommended System Requirements

- **CPU:** 8+ cores, modern x86_64 with AVX2
- **RAM:** 16GB+ for high-performance testing
- **Storage:** SSD for logs and temporary files
- **Network:** 10Gbps+ interface for maximum performance
- **OS:** Linux 5.4+, Windows 11, macOS 12+

### Privileges Required

| Operation             | Linux | Windows       | macOS |
| --------------------- | ----- | ------------- | ----- |
| **Basic UDP/TCP**     | User  | User          | User  |
| **Raw Sockets**       | Root  | Administrator | Root  |
| **Advanced Backends** | Root  | Administrator | Root  |
| **System Tuning**     | Root  | Administrator | Root  |

## Known Limitations

### General Limitations

- **Localhost Testing:** Performance against 127.0.0.1 measures memory speed, not network performance
- **Single Machine:** Cannot simulate true distributed attacks without multiple systems
- **Python GIL:** Limits CPU-bound parallelism in Python mode
- **Memory Usage:** High memory consumption during sustained high-rate attacks

### Platform-Specific Limitations

#### Linux

- **DPDK:** Requires hugepage configuration and compatible NICs
- **AF_XDP:** Requires recent kernel and proper XDP program loading
- **Root Access:** Many advanced features require root privileges

#### Windows

- **Raw Sockets:** Limited compared to Linux, may require special configuration
- **Windows Defender:** May flag the tool as potentially unwanted
- **Performance:** Generally lower than Linux due to network stack differences

#### macOS

- **SIP:** System Integrity Protection may interfere with some operations
- **Raw Sockets:** Require root access and may have additional restrictions
- **Performance:** Limited by macOS network stack design

## Troubleshooting

### Common Issues

#### "Native engine not available"

```bash
cd native/rust_engine
maturin develop --release
```

#### "Permission denied" for raw sockets

```bash
# Linux/macOS
sudo python ddos.py [options]

# Windows (run as Administrator)
python ddos.py [options]
```

#### Low performance

```bash
# Linux kernel tuning
sudo sysctl -w net.core.rmem_max=268435456
sudo sysctl -w net.core.wmem_max=268435456
sudo sysctl -w net.ipv4.tcp_timestamps=0

# Check available backends
python -c "from core.native_engine import get_capabilities; print(get_capabilities())"
```

### Performance Optimization

#### Linux

```bash
# Increase socket buffers
echo 'net.core.rmem_max = 268435456' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' >> /etc/sysctl.conf

# Disable unnecessary features
echo 'net.ipv4.tcp_timestamps = 0' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_sack = 0' >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

#### Windows

```powershell
# Increase socket buffers (requires registry edit)
# Run as Administrator
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global chimney=enabled
```

#### macOS

```bash
# Increase socket buffers
sudo sysctl -w net.inet.tcp.sendspace=1048576
sudo sysctl -w net.inet.tcp.recvspace=1048576
```

## Compliance and Safety

### Built-in Safety Features

- **Target Validation:** Whitelist-based authorization
- **Rate Limiting:** Engine-level rate enforcement
- **Resource Monitoring:** Auto-throttling on resource exhaustion
- **Emergency Stop:** 100ms shutdown guarantee
- **Audit Logging:** Tamper-evident logs with hash chains

### Legal Compliance

- **Authorization Required:** Only test systems you own or have explicit permission to test
- **Logging:** All activities are logged for audit purposes
- **Responsible Use:** Tool includes safety controls to prevent misuse

## Getting Help

### Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Usage Guide](docs/USAGE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [API Reference](docs/API_REFERENCE.md)

### System Status

```bash
# Check system capabilities
python ddos.py --status

# Check native engine availability
python -c "from core.native_engine import get_capabilities; print(get_capabilities())"

# Run comprehensive test
python comprehensive_stress_test.py
```

### Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive guides and examples
- Community: Share experiences and best practices

---

**Last Updated:** December 2024  
**Version:** 2.0.0  
**Platforms Tested:** Linux (Ubuntu 20.04+, CentOS 8+), Windows 10/11, macOS 12+
